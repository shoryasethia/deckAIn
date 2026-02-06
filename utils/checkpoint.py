"""
deckAIn - Checkpoint/Cache Manager
Saves intermediate results to resume from last successful stage
"""

import json
import pickle
from pathlib import Path
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class CheckpointManager:
    """Manages pipeline checkpoints for resuming failed runs."""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize checkpoint manager.
        
        Args:
            cache_dir: Directory to store checkpoint files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"CheckpointManager initialized (cache: {self.cache_dir})")
    
    def save_checkpoint(self, stage: str, data: dict, run_id: str):
        """
        Save checkpoint for a stage.
        
        Args:
            stage: Stage name (e.g., "private_data", "content", "images")
            data: Data to save
            run_id: Unique run identifier
        """
        checkpoint_file = self.cache_dir / f"{run_id}_{stage}.pkl"
        
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump({
                    "stage": stage,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }, f)
            logger.info(f"Checkpoint saved: {stage}")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint {stage}: {e}")
    
    def load_checkpoint(self, stage: str, run_id: str):
        """
        Load checkpoint for a stage.
        
        Args:
            stage: Stage name
            run_id: Unique run identifier
        
        Returns:
            Saved data or None if not found
        """
        checkpoint_file = self.cache_dir / f"{run_id}_{stage}.pkl"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'rb') as f:
                checkpoint = pickle.load(f)
            logger.info(f"Loaded checkpoint: {stage} (from {checkpoint['timestamp']})")
            return checkpoint['data']
        except Exception as e:
            logger.warning(f"Failed to load checkpoint {stage}: {e}")
            return None
    
    def get_run_id(self, markdown_path: str) -> str:
        """
        Generate run ID from markdown path.
        
        Args:
            markdown_path: Path to markdown file
        
        Returns:
            Run ID string
        """
        return Path(markdown_path).stem
    
    def clear_checkpoints(self, run_id: str):
        """
        Clear all checkpoints for a run.
        
        Args:
            run_id: Unique run identifier
        """
        for checkpoint_file in self.cache_dir.glob(f"{run_id}_*.pkl"):
            checkpoint_file.unlink()
        logger.info(f"Cleared checkpoints for run: {run_id}")
    
    def list_checkpoints(self, run_id: str) -> list:
        """
        List available checkpoints for a run.
        
        Args:
            run_id: Unique run identifier
        
        Returns:
            List of stage names
        """
        stages = []
        for checkpoint_file in self.cache_dir.glob(f"{run_id}_*.pkl"):
            stage = checkpoint_file.stem.replace(f"{run_id}_", "")
            stages.append(stage)
        return stages
