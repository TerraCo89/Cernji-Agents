"""
Validation node.

Validates resume quality and checks for common issues.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import ResumeState
from ..config import get_settings
from ..prompts import VALIDATION_PROMPT, SYSTEM_RESUME_EXPERT


def validate_resume(state: ResumeState) -> dict:
    """
    Validate resume for quality, formatting, and common errors.
    
    Args:
        state: Current resume agent state
        
    Returns:
        State updates with validation results
    """
    print("\n✅ Validating resume quality...")
    
    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.model_name,
        temperature=0.0,  # Deterministic for validation
        max_tokens=2048,
    )
    
    # Get the current resume (optimized if available)
    resume_text = state['resume_text']
    if state.get('optimized_sections'):
        resume_text = state['optimized_sections'][-1]['content']
    
    # Prepare validation prompt
    prompt = VALIDATION_PROMPT.format(resume_text=resume_text)
    
    # Run validation
    response = llm.invoke([
        SystemMessage(content=SYSTEM_RESUME_EXPERT),
        HumanMessage(content=prompt)
    ])
    
    validation_result = response.content
    
    # Parse errors and warnings (simplified - use structured outputs in production)
    errors = _extract_validation_items(validation_result, "error")
    warnings = _extract_validation_items(validation_result, "warning")
    
    # Update suggestions with validation findings
    suggestions = list(state.get('optimization_suggestions', []))
    
    if errors:
        suggestions.extend([f"Error: {e}" for e in errors])
    if warnings:
        suggestions.extend([f"Warning: {w}" for w in warnings])
    
    # Determine if manual review is needed
    needs_review = (
        state.get('needs_manual_review', False) or
        len(errors) > 0 or
        len(warnings) > 3
    )
    
    print(f"   ✓ Errors: {len(errors)}")
    print(f"   ✓ Warnings: {len(warnings)}")
    
    return {
        "optimization_suggestions": suggestions,
        "needs_manual_review": needs_review,
    }


def await_reviewer_approval(state: ResumeState) -> dict:
    """
    Human-in-the-loop checkpoint for manual review.
    
    This node pauses execution to allow a human reviewer to approve changes.
    In production, this would integrate with a UI or notification system.
    
    Args:
        state: Current resume agent state
        
    Returns:
        Empty dict (checkpoint pauses here)
    """
    print("\n⏸️  CHECKPOINT: Awaiting human reviewer approval...")
    print(f"   ATS Score: {state['ats_score']}/100")
    print(f"   Suggestions: {len(state.get('optimization_suggestions', []))}")
    
    # In production:
    # - Send notification to reviewer
    # - Display optimized resume in UI
    # - Wait for approval/rejection
    # - Allow reviewer to make manual edits
    
    return {}


def finalize_resume(state: ResumeState) -> dict:
    """
    Finalize the resume after approval.
    
    Args:
        state: Current resume agent state
        
    Returns:
        State updates with final resume
    """
    print("\n📝 Finalizing resume...")
    
    # Get the optimized resume
    if state.get('optimized_sections'):
        final_resume = state['optimized_sections'][-1]['content']
    else:
        final_resume = state['resume_text']
    
    print(f"   ✓ Final ATS Score: {state['ats_score']}/100")
    print("   ✓ Resume finalized and ready for submission")
    
    return {
        "final_resume": final_resume,
        "reviewer_approved": True,
    }


# Helper function
def _extract_validation_items(text: str, item_type: str) -> list[str]:
    """Extract validation errors or warnings from text."""
    items = []
    in_section = False
    
    for line in text.split('\n'):
        line = line.strip()
        
        # Check if we're entering the section
        if item_type.lower() in line.lower() and ':' in line:
            in_section = True
            continue
        
        # Check if we're leaving the section
        if in_section and line and ':' in line and item_type.lower() not in line.lower():
            break
        
        # Extract item
        if in_section and line:
            cleaned = line.lstrip('-•*123456789. ')
            if cleaned and len(cleaned) > 5:
                items.append(cleaned)
    
    return items[:10]  # Limit to top 10
