"""
Resume Blocks API - Editor Endpoints (Step 8)

Provides CRUD operations for resume blocks and AI-powered rewriting.
All AI rewrites go through Truth Guard (Step 7) to prevent hallucinations.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dependencies.auth import get_current_user
from services.supabase_client import get_supabase_client
from services.block_editor_service import BlockEditorService


router = APIRouter(prefix="/api/resume-blocks", tags=["blocks"])


class UpdateBlockRequest(BaseModel):
    """Request to manually update a block."""
    content: Dict[str, Any] = Field(..., description="Block content (JSONB)")
    block_type: Optional[str] = Field(None, description="Block type (paragraph, bullet, etc.)")


class AIRewriteRequest(BaseModel):
    """Request for AI-powered rewrite."""
    instruction: str = Field(..., description="Rewrite instruction: shorten|expand|fix_grammar|improve")
    context: Optional[str] = Field(None, description="Additional context for the rewrite")


class ReorderBlocksRequest(BaseModel):
    """Request to reorder blocks within a section."""
    block_ids: List[str] = Field(..., description="List of block IDs in new order")


class BlockResponse(BaseModel):
    """Response for a single block."""
    id: str
    resume_version_id: str
    section_id: str
    user_id: str
    block_type: str
    content: Dict[str, Any]
    sort_order: int
    created_at: str
    updated_at: str


class AIRewriteResponse(BaseModel):
    """Response for AI rewrite."""
    original_text: str
    proposed_text: str
    verification_status: str  # supported, partially_supported, unsupported
    guardrails_passed: bool
    reasoning: str
    warnings: List[str]  # Any warnings from Truth Guard


@router.get("/{block_id}", response_model=BlockResponse)
async def get_block(
    block_id: UUID,
    user: dict = Depends(get_current_user)
):
    """Get a single block by ID."""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("resume_blocks").select(
            "*"
        ).eq("id", str(block_id)).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Block not found"
            )
        
        return BlockResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get block: {str(e)}"
        )


@router.patch("/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: UUID,
    request: UpdateBlockRequest,
    user: dict = Depends(get_current_user)
):
    """
    Manually update a block (inline editing).
    
    This is for direct user edits in the editor, NOT AI-generated changes.
    AI rewrites should use POST /{block_id}/ai-rewrite.
    """
    try:
        supabase = get_supabase_client()
        service = BlockEditorService(supabase)
        
        # Verify block ownership
        block = supabase.table("resume_blocks").select(
            "*"
        ).eq("id", str(block_id)).eq("user_id", user["id"]).execute()
        
        if not block.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Block not found"
            )
        
        # Update block
        result = await service.update_block(
            block_id=str(block_id),
            content=request.content,
            block_type=request.block_type,
            user_id=user["id"]
        )
        
        return BlockResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update block: {str(e)}"
        )


@router.post("/{block_id}/ai-rewrite", response_model=AIRewriteResponse)
async def ai_rewrite_block(
    block_id: UUID,
    request: AIRewriteRequest,
    user: dict = Depends(get_current_user)
):
    """
    AI-powered rewrite of a block.
    
    Instructions:
    - shorten: Make more concise
    - expand: Add more detail (from fact ledger only)
    - fix_grammar: Fix grammar and punctuation
    - improve: Better action verbs and phrasing
    
    All rewrites go through Truth Guard (Step 7):
    - Constrained generation (fact traceability)
    - Independent verification (Haiku)
    - Deterministic guardrails (hard blocks)
    
    Returns proposed rewrite with verification status.
    User must explicitly apply if verification_status is 'partially_supported'.
    """
    try:
        # Validate instruction
        valid_instructions = ["shorten", "expand", "fix_grammar", "improve"]
        if request.instruction not in valid_instructions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid instruction. Must be one of: {', '.join(valid_instructions)}"
            )
        
        supabase = get_supabase_client()
        service = BlockEditorService(supabase)
        
        # Verify block ownership
        block = supabase.table("resume_blocks").select(
            "*"
        ).eq("id", str(block_id)).eq("user_id", user["id"]).execute()
        
        if not block.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Block not found"
            )
        
        # Get fact ledger for this resume version
        resume_version_id = block.data[0]["resume_version_id"]
        
        # Perform AI rewrite with Truth Guard
        result = await service.ai_rewrite_block(
            block_id=str(block_id),
            instruction=request.instruction,
            context=request.context,
            user_id=user["id"],
            resume_version_id=resume_version_id
        )
        
        return AIRewriteResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI rewrite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rewrite block: {str(e)}"
        )


@router.post("/{block_id}/apply-rewrite", response_model=BlockResponse)
async def apply_ai_rewrite(
    block_id: UUID,
    proposed_text: str,
    user: dict = Depends(get_current_user)
):
    """
    Apply an AI-generated rewrite to a block.
    
    This should only be called after ai_rewrite_block returns a successful result.
    """
    try:
        supabase = get_supabase_client()
        service = BlockEditorService(supabase)
        
        # Verify block ownership
        block = supabase.table("resume_blocks").select(
            "*"
        ).eq("id", str(block_id)).eq("user_id", user["id"]).execute()
        
        if not block.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Block not found"
            )
        
        # Apply the rewrite
        result = await service.apply_rewrite(
            block_id=str(block_id),
            proposed_text=proposed_text,
            user_id=user["id"]
        )
        
        return BlockResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error applying rewrite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply rewrite: {str(e)}"
        )


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_block(
    block_id: UUID,
    user: dict = Depends(get_current_user)
):
    """Delete a block."""
    try:
        supabase = get_supabase_client()
        
        # Verify block ownership
        block = supabase.table("resume_blocks").select(
            "*"
        ).eq("id", str(block_id)).eq("user_id", user["id"]).execute()
        
        if not block.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Block not found"
            )
        
        # Delete block
        supabase.table("resume_blocks").delete().eq(
            "id", str(block_id)
        ).eq("user_id", user["id"]).execute()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete block: {str(e)}"
        )


@router.post("/sections/{section_id}/reorder", status_code=status.HTTP_200_OK)
async def reorder_blocks(
    section_id: UUID,
    request: ReorderBlocksRequest,
    user: dict = Depends(get_current_user)
):
    """
    Reorder blocks within a section.
    
    Provide list of block IDs in the new desired order.
    """
    try:
        supabase = get_supabase_client()
        service = BlockEditorService(supabase)
        
        # Verify section ownership
        section = supabase.table("resume_sections").select(
            "*"
        ).eq("id", str(section_id)).eq("user_id", user["id"]).execute()
        
        if not section.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        # Reorder blocks
        await service.reorder_blocks(
            section_id=str(section_id),
            block_ids=request.block_ids,
            user_id=user["id"]
        )
        
        return {"success": True, "message": "Blocks reordered successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reordering blocks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder blocks: {str(e)}"
        )


@router.post("/sections/{section_id}/blocks", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(
    section_id: UUID,
    content: Dict[str, Any],
    block_type: str = "paragraph",
    user: dict = Depends(get_current_user)
):
    """Create a new block in a section."""
    try:
        supabase = get_supabase_client()
        service = BlockEditorService(supabase)
        
        # Verify section ownership
        section = supabase.table("resume_sections").select(
            "*"
        ).eq("id", str(section_id)).eq("user_id", user["id"]).execute()
        
        if not section.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        resume_version_id = section.data[0]["resume_version_id"]
        
        # Create block
        result = await service.create_block(
            section_id=str(section_id),
            resume_version_id=resume_version_id,
            content=content,
            block_type=block_type,
            user_id=user["id"]
        )
        
        return BlockResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create block: {str(e)}"
        )
