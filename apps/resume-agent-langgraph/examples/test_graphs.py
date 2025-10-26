"""
Tests for graph implementations.
"""

import pytest
from resume_agent.graphs import create_resume_agent_graph, compile_resume_agent
from resume_agent.state import ResumeState


class TestGraphStructure:
    """Tests for graph structure and compilation."""
    
    def test_create_graph_succeeds(self):
        """Test that graph creation succeeds."""
        graph = create_resume_agent_graph()
        
        assert graph is not None
        # Check that nodes were added
        assert hasattr(graph, 'nodes')
    
    def test_compile_graph_succeeds(self):
        """Test that graph compilation succeeds."""
        app = compile_resume_agent(checkpointing=False)
        
        assert app is not None
    
    def test_compile_graph_with_checkpointing(self):
        """Test graph compilation with checkpointing."""
        app = compile_resume_agent(checkpointing=True)
        
        assert app is not None


class TestGraphExecution:
    """Tests for graph execution."""
    
    @pytest.fixture
    def minimal_state(self):
        """Create minimal valid state for testing."""
        return {
            "resume_text": "Test resume",
            "job_posting_url": "https://example.com/job",
            "job_title": "",
            "job_requirements": [],
            "job_skills": [],
            "ats_keywords": [],
            "current_skills": [],
            "experience_summary": "",
            "skill_gaps": [],
            "optimized_sections": [],
            "ats_score": 0,
            "optimization_suggestions": [],
            "needs_manual_review": False,
            "reviewer_approved": False,
            "iteration_count": 0,
            "max_iterations": 1,  # Minimal iterations for testing
            "final_resume": "",
            "cover_letter": "",
        }
    
    def test_graph_execution_structure(self, minimal_state):
        """Test that graph can be invoked (structure test, not full execution)."""
        pytest.skip("Requires API key and mocking - structure test only")
        
        app = compile_resume_agent(checkpointing=False)
        
        # This would test actual execution with mocked LLM responses
        # result = app.invoke(minimal_state)
        # assert "final_resume" in result


class TestConditionalRouting:
    """Tests for conditional routing logic."""
    
    def test_should_iterate_max_iterations(self):
        """Test that iteration stops at max_iterations."""
        from resume_agent.graphs.main import should_iterate
        
        state = {
            "iteration_count": 3,
            "max_iterations": 3,
            "ats_score": 50,
        }
        
        result = should_iterate(state)
        assert result == "validate"
    
    def test_should_iterate_high_score(self):
        """Test that iteration stops when ATS score is high enough."""
        from resume_agent.graphs.main import should_iterate
        
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "ats_score": 85,  # Above threshold
        }
        
        result = should_iterate(state)
        assert result == "validate"
    
    def test_should_iterate_continue(self):
        """Test that iteration continues when conditions aren't met."""
        from resume_agent.graphs.main import should_iterate
        
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "ats_score": 60,  # Below threshold
        }
        
        result = should_iterate(state)
        assert result == "optimize"
    
    def test_should_review_when_needed(self):
        """Test manual review routing."""
        from resume_agent.graphs.main import should_review
        
        state = {
            "needs_manual_review": True,
        }
        
        result = should_review(state)
        assert result == "await_approval"
    
    def test_should_skip_review(self):
        """Test skipping manual review."""
        from resume_agent.graphs.main import should_review
        from resume_agent.config import Settings
        
        # Mock settings to not require review
        Settings.require_manual_review = False
        
        state = {
            "needs_manual_review": False,
        }
        
        result = should_review(state)
        assert result == "finalize"


class TestStateTransitions:
    """Tests for state transitions."""
    
    def test_increment_iteration(self):
        """Test iteration counter increment."""
        from resume_agent.graphs.main import increment_iteration
        
        state = {"iteration_count": 0}
        result = increment_iteration(state)
        
        assert result["iteration_count"] == 1
    
    def test_increment_iteration_from_existing(self):
        """Test iteration counter increment from existing value."""
        from resume_agent.graphs.main import increment_iteration
        
        state = {"iteration_count": 2}
        result = increment_iteration(state)
        
        assert result["iteration_count"] == 3


# Integration test
class TestEndToEndFlow:
    """End-to-end integration tests."""
    
    def test_full_pipeline_mock(self):
        """Test full pipeline with mocked components."""
        pytest.skip("Integration test requiring full mocking setup")
        
        # This would test:
        # 1. Job posting analysis
        # 2. Resume analysis
        # 3. Optimization iterations
        # 4. Validation
        # 5. Checkpoint
        # 6. Finalization
        pass
