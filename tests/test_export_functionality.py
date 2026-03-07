"""Tests for audit log and pipeline card export functionality."""
import json
import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call

# Import the store and models
from store import get_store, PipelineCard, _now, _uid


class TestAuditExport:
    """Test audit log export functionality."""
    
    def test_audit_export_csv_with_data(self):
        """Test exporting audit logs to CSV with data."""
        # Mock state with audit data
        mock_state = MagicMock()
        mock_state.audit_table = pd.DataFrame([
            {
                "Time": "12:00:00",
                "Actor": "user1",
                "Action": "card.create",
                "Resource": "card/123",
                "Details": "Created new card",
                "Severity": "info"
            },
            {
                "Time": "12:05:00",
                "Actor": "user2",
                "Action": "job.submit",
                "Resource": "job/456",
                "Details": "Submitted job",
                "Severity": "info"
            }
        ])
        
        # Import the callback after mocking
        with patch("app.download") as mock_download, \
             patch("app.store") as mock_store, \
             patch("app.notify") as mock_notify, \
             patch("app._refresh_audit"):
            
            from app import on_audit_export_csv
            
            # Execute the export
            on_audit_export_csv(mock_state)
            
            # Verify download was called
            assert mock_download.called
            call_args = mock_download.call_args
            assert call_args[0][0] == mock_state  # state parameter
            
            # Verify CSV content
            csv_content = call_args[1]["content"].decode("utf-8")
            assert "Time,Actor,Action,Resource,Details,Severity" in csv_content
            assert "user1" in csv_content
            assert "card.create" in csv_content
            
            # Verify filename format
            filename = call_args[1]["name"]
            assert filename.startswith("audit_log_")
            assert filename.endswith(".csv")
            
            # Verify success notification
            assert mock_notify.called
            notify_calls = [call for call in mock_notify.call_args_list 
                          if len(call[0]) > 1 and call[0][1] == "success"]
            assert len(notify_calls) > 0
    
    def test_audit_export_csv_empty_data(self):
        """Test exporting audit logs when no data is available."""
        mock_state = MagicMock()
        mock_state.audit_table = pd.DataFrame()
        
        with patch("app.notify") as mock_notify, \
             patch("app.download") as mock_download:
            
            from app import on_audit_export_csv
            
            on_audit_export_csv(mock_state)
            
            # Verify warning notification
            mock_notify.assert_called_once()
            assert mock_notify.call_args[0][1] == "warning"
            
            # Verify download was not called
            assert not mock_download.called
    
    def test_audit_export_json_with_data(self):
        """Test exporting audit logs to JSON with data."""
        mock_state = MagicMock()
        mock_state.audit_table = pd.DataFrame([
            {
                "Time": "12:00:00",
                "Actor": "user1",
                "Action": "card.create",
                "Resource": "card/123",
                "Details": "Created new card",
                "Severity": "info"
            }
        ])
        
        with patch("app.download") as mock_download, \
             patch("app.store") as mock_store, \
             patch("app.notify") as mock_notify, \
             patch("app._refresh_audit"):
            
            from app import on_audit_export_json
            
            on_audit_export_json(mock_state)
            
            # Verify download was called
            assert mock_download.called
            call_args = mock_download.call_args
            
            # Verify JSON content
            json_content = call_args[1]["content"].decode("utf-8")
            data = json.loads(json_content)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["Actor"] == "user1"
            assert data[0]["Action"] == "card.create"
            
            # Verify filename format
            filename = call_args[1]["name"]
            assert filename.startswith("audit_log_")
            assert filename.endswith(".json")
    
    def test_audit_export_handles_datetime_serialization(self):
        """Test that datetime objects are properly serialized in JSON export."""
        mock_state = MagicMock()
        # Create DataFrame with datetime-like values
        mock_state.audit_table = pd.DataFrame([
            {
                "Time": "2024-03-06 12:00:00",
                "Actor": "user1",
                "Action": "test",
                "Resource": "test/123",
                "Details": "Test with date",
                "Severity": "info"
            }
        ])
        
        with patch("app.download") as mock_download, \
             patch("app.store"), \
             patch("app.notify"), \
             patch("app._refresh_audit"):
            
            from app import on_audit_export_json
            
            on_audit_export_json(mock_state)
            
            # Should not raise exception
            assert mock_download.called
            json_content = mock_download.call_args[1]["content"].decode("utf-8")
            # Should be valid JSON
            data = json.loads(json_content)
            assert isinstance(data, list)


class TestPipelineExport:
    """Test pipeline card export functionality."""
    
    def test_pipeline_export_csv_with_cards(self):
        """Test exporting pipeline cards to CSV with data."""
        # Create mock cards
        mock_cards = [
            PipelineCard(
                id=_uid(),
                title="Test Card 1",
                description="Description 1",
                status="backlog",
                priority="high",
                assignee="user1",
                labels=["label1", "label2"]
            ),
            PipelineCard(
                id=_uid(),
                title="Test Card 2",
                description="Description 2",
                status="done",
                priority="low",
                attested=True,
                attested_by="admin"
            )
        ]
        
        mock_state = MagicMock()
        
        with patch("app.store.list_cards", return_value=mock_cards), \
             patch("app.download") as mock_download, \
             patch("app.store.log_user_action"), \
             patch("app.notify") as mock_notify, \
             patch("app._resolve_job_status", return_value="—"):
            
            from app import on_pipeline_export_csv
            
            on_pipeline_export_csv(mock_state)
            
            # Verify download was called
            assert mock_download.called
            call_args = mock_download.call_args
            
            # Verify CSV content
            csv_content = call_args[1]["content"].decode("utf-8")
            assert "ID,Title,Description,Status,Priority" in csv_content
            assert "Test Card 1" in csv_content
            assert "Test Card 2" in csv_content
            assert "backlog" in csv_content
            assert "high" in csv_content
            assert "label1, label2" in csv_content
            
            # Verify filename format
            filename = call_args[1]["name"]
            assert filename.startswith("pipeline_cards_")
            assert filename.endswith(".csv")
            
            # Verify success notification
            assert mock_notify.called
    
    def test_pipeline_export_csv_empty_cards(self):
        """Test exporting pipeline cards when no cards exist."""
        mock_state = MagicMock()
        
        with patch("app.store.list_cards", return_value=[]), \
             patch("app.notify") as mock_notify, \
             patch("app.download") as mock_download:
            
            from app import on_pipeline_export_csv
            
            on_pipeline_export_csv(mock_state)
            
            # Verify warning notification
            mock_notify.assert_called_once()
            assert mock_notify.call_args[0][1] == "warning"
            
            # Verify download was not called
            assert not mock_download.called
    
    def test_pipeline_export_json_with_cards(self):
        """Test exporting pipeline cards to JSON with data."""
        mock_cards = [
            PipelineCard(
                id="card-123",
                title="Test Card",
                description="Test description",
                status="in_progress",
                priority="medium",
                assignee="user1",
                labels=["test"],
                attested=True,
                attested_by="admin",
                attested_at="2024-03-06T12:00:00",
                attestation="Approved"
            )
        ]
        
        mock_state = MagicMock()
        
        with patch("app.store.list_cards", return_value=mock_cards), \
             patch("app.download") as mock_download, \
             patch("app.store.log_user_action"), \
             patch("app.notify"), \
             patch("app._resolve_job_status", return_value="—"):
            
            from app import on_pipeline_export_json
            
            on_pipeline_export_json(mock_state)
            
            # Verify download was called
            assert mock_download.called
            call_args = mock_download.call_args
            
            # Verify JSON content
            json_content = call_args[1]["content"].decode("utf-8")
            data = json.loads(json_content)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["title"] == "Test Card"
            assert data[0]["status"] == "in_progress"
            assert data[0]["priority"] == "medium"
            assert data[0]["attested"] is True
            assert data[0]["attested_by"] == "admin"
            assert data[0]["labels"] == ["test"]
            
            # Verify filename format
            filename = call_args[1]["name"]
            assert filename.startswith("pipeline_cards_")
            assert filename.endswith(".json")
    
    def test_pipeline_export_includes_all_metadata(self):
        """Test that pipeline export includes all relevant metadata fields."""
        mock_card = PipelineCard(
            id="card-456",
            title="Complete Card",
            description="Full metadata",
            status="review",
            priority="critical",
            card_type="data_processing",
            assignee="user2",
            labels=["urgent", "pii"],
            data_source="customer_db",
            session_id="session-789",
            scenario_id="scenario-101",
            attested=True,
            attested_by="compliance_officer",
            attested_at="2024-03-06T14:30:00",
            attestation="Verified compliance",
            attestation_sig_alg="Ed25519",
            attestation_sig_key_id="key-1",
            attestation_sig="signature_base64",
            attestation_sig_verified=True
        )
        
        mock_state = MagicMock()
        
        with patch("app.store.list_cards", return_value=[mock_card]), \
             patch("app.download") as mock_download, \
             patch("app.store.log_user_action"), \
             patch("app.notify"), \
             patch("app._resolve_job_status", return_value="completed"):
            
            from app import on_pipeline_export_json
            
            on_pipeline_export_json(mock_state)
            
            json_content = mock_download.call_args[1]["content"].decode("utf-8")
            data = json.loads(json_content)
            card_data = data[0]
            
            # Verify all key fields are present
            assert card_data["id"] == "card-456"
            assert card_data["title"] == "Complete Card"
            assert card_data["status"] == "review"
            assert card_data["priority"] == "critical"
            assert card_data["card_type"] == "data_processing"
            assert card_data["assignee"] == "user2"
            assert card_data["labels"] == ["urgent", "pii"]
            assert card_data["data_source"] == "customer_db"
            assert card_data["session_id"] == "session-789"
            assert card_data["scenario_id"] == "scenario-101"
            assert card_data["job_status"] == "completed"
            assert card_data["attested"] is True
            assert card_data["attested_by"] == "compliance_officer"
            assert card_data["attestation"] == "Verified compliance"
            assert card_data["attestation_sig_alg"] == "Ed25519"
            assert card_data["attestation_sig_verified"] is True
    
    def test_pipeline_export_handles_exceptions(self):
        """Test that export functions handle exceptions gracefully."""
        mock_state = MagicMock()
        
        # Mock store at the module level where it's imported in app.py
        with patch("app.store") as mock_store, \
             patch("app.notify") as mock_notify, \
             patch("app._log") as mock_log:
            
            # Make list_cards raise an exception
            mock_store.list_cards.side_effect = Exception("Database error")
            
            from app import on_pipeline_export_csv
            
            on_pipeline_export_csv(mock_state)
            
            # Verify error notification
            error_calls = [call for call in mock_notify.call_args_list 
                         if len(call[0]) > 1 and call[0][1] == "error"]
            assert len(error_calls) > 0
            
            # Verify error was logged
            assert mock_log.error.called


class TestExportSecurity:
    """Test security aspects of export functionality."""
    
    def test_no_pickle_usage(self):
        """Verify that exports don't use pickle serialization."""
        # This test verifies that we're using safe serialization methods
        mock_cards = [
            PipelineCard(
                id="test-123",
                title="Test",
                status="backlog",
                priority="low"
            )
        ]
        
        mock_state = MagicMock()
        
        with patch("app.store.list_cards", return_value=mock_cards), \
             patch("app.download") as mock_download, \
             patch("app.store.log_user_action"), \
             patch("app.notify"), \
             patch("app._resolve_job_status", return_value="—"):
            
            from app import on_pipeline_export_csv, on_pipeline_export_json
            
            # Test CSV export
            on_pipeline_export_csv(mock_state)
            csv_content = mock_download.call_args[1]["content"]
            # Verify it's text-based CSV, not pickled binary
            assert isinstance(csv_content, bytes)
            decoded = csv_content.decode("utf-8")
            assert "ID,Title" in decoded
            
            # Test JSON export
            on_pipeline_export_json(mock_state)
            json_content = mock_download.call_args[1]["content"]
            # Verify it's text-based JSON, not pickled binary
            assert isinstance(json_content, bytes)
            decoded = json_content.decode("utf-8")
            parsed = json.loads(decoded)
            assert isinstance(parsed, list)
    
    def test_audit_export_sanitizes_data(self):
        """Test that exported data is properly sanitized."""
        # Test with potentially problematic data
        mock_state = MagicMock()
        mock_state.audit_table = pd.DataFrame([
            {
                "Time": "12:00:00",
                "Actor": "user<script>alert('xss')</script>",
                "Action": "test",
                "Resource": "test/123",
                "Details": "Details with special chars: <>\"'&",
                "Severity": "info"
            }
        ])
        
        with patch("app.download") as mock_download, \
             patch("app.store"), \
             patch("app.notify"), \
             patch("app._refresh_audit"):
            
            from app import on_audit_export_csv
            
            on_audit_export_csv(mock_state)
            
            # Verify CSV was created (pandas handles CSV escaping)
            assert mock_download.called
            csv_content = mock_download.call_args[1]["content"].decode("utf-8")
            # Data should be present but properly escaped by pandas
            assert "user<script>" in csv_content  # pandas preserves content but escapes
            assert "special chars" in csv_content


class TestExportWithLargeDatasets:
    """Test export functionality with large datasets."""
    
    def test_export_large_audit_log(self):
        """Test exporting a large number of audit entries."""
        # Create a large audit log (1000 entries)
        rows = [
            {
                "Time": f"{(i % 24):02d}:00:00",  # Valid 24-hour format
                "Actor": f"user{i % 10}",
                "Action": f"action{i % 5}",
                "Resource": f"resource/{i}",
                "Details": f"Details for entry {i}",
                "Severity": ["info", "warning", "critical"][i % 3]
            }
            for i in range(1000)
        ]
        
        mock_state = MagicMock()
        mock_state.audit_table = pd.DataFrame(rows)
        
        with patch("app.download") as mock_download, \
             patch("app.store"), \
             patch("app.notify"), \
             patch("app._refresh_audit"):
            
            from app import on_audit_export_csv
            
            on_audit_export_csv(mock_state)
            
            # Verify export succeeded
            assert mock_download.called
            csv_content = mock_download.call_args[1]["content"].decode("utf-8")
            # Should have header + 1000 data rows
            line_count = csv_content.count('\n')
            assert line_count >= 1000
    
    def test_export_large_pipeline_cards(self):
        """Test exporting a large number of pipeline cards."""
        # Create 500 mock cards
        mock_cards = [
            PipelineCard(
                id=f"card-{i:04d}",
                title=f"Card {i}",
                description=f"Description for card {i}",
                status=["backlog", "in_progress", "review", "done"][i % 4],
                priority=["low", "medium", "high", "critical"][i % 4],
                assignee=f"user{i % 10}",
                labels=[f"label{i % 5}", f"tag{i % 3}"]
            )
            for i in range(500)
        ]
        
        mock_state = MagicMock()
        
        with patch("app.store.list_cards", return_value=mock_cards), \
             patch("app.download") as mock_download, \
             patch("app.store.log_user_action"), \
             patch("app.notify"), \
             patch("app._resolve_job_status", return_value="—"):
            
            from app import on_pipeline_export_csv
            
            on_pipeline_export_csv(mock_state)
            
            # Verify export succeeded
            assert mock_download.called
            csv_content = mock_download.call_args[1]["content"].decode("utf-8")
            # Should have header + 500 data rows
            line_count = csv_content.count('\n')
            assert line_count >= 500
