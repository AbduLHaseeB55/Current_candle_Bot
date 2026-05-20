"""
Model Inference Module
Loads and runs the LSTM model for candle close prediction
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CandleLSTM(nn.Module):
    """
    LSTM model for predicting candle close direction.
    Input: (batch, sequence_length, features)
    Output: probability of green candle
    """
    
    def __init__(
        self,
        input_size: int = 27,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        """
        Initialize LSTM model.
        
        Args:
            input_size: Number of input features
            hidden_size: LSTM hidden dimension
            num_layers: Number of LSTM layers
            dropout: Dropout rate
        """
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch, sequence_length, features)
            
        Returns:
            Probability of green candle (batch, 1)
        """
        # LSTM forward pass
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Use the last hidden state
        last_hidden = h_n[-1]  # Shape: (batch, hidden_size)
        
        # Fully connected layers
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.sigmoid(out)
        
        return out


class ModelInference:
    """
    Handles model loading and inference with confidence smoothing.
    """
    
    def __init__(
        self,
        model_path: str,
        device: Optional[str] = None,
        smooth_alpha: float = 0.25
    ):
        """
        Initialize model inference.
        
        Args:
            model_path: Path to the saved model file
            device: Device to run inference on ('cuda' or 'cpu')
            smooth_alpha: Smoothing factor for confidence (0-1)
        """
        self.model_path = model_path
        self.smooth_alpha = smooth_alpha
        
        # Determine device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        logger.info(f"Using device: {self.device}")
        
        # Model will be loaded lazily
        self.model = None
        self.last_prob_up = 0.5  # For smoothing
        
    def load_model(self, input_size: int = 27) -> bool:
        """
        Load the model from disk.
        
        Args:
            input_size: Number of input features
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            model_path = Path(self.model_path)
            
            if not model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                logger.info("Creating untrained model for testing...")
                self.model = CandleLSTM(input_size=input_size)
                self.model.to(self.device)
                self.model.eval()
                return True
            
            # Load model
            self.model = CandleLSTM(input_size=input_size)
            
            # Load state dict
            state_dict = torch.load(model_path, map_location=self.device)
            
            # Handle different save formats
            if 'model_state_dict' in state_dict:
                self.model.load_state_dict(state_dict['model_state_dict'])
            else:
                self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Model loaded successfully from {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, features: np.ndarray) -> Optional[Tuple[float, float]]:
        """
        Run inference on features.
        
        Args:
            features: NumPy array of shape (sequence_length, num_features)
            
        Returns:
            Tuple of (prob_up, prob_up_smoothed) or None if error
        """
        if self.model is None:
            logger.error("Model not loaded. Call load_model() first.")
            return None
        
        try:
            # Convert to tensor and add batch dimension
            x = torch.from_numpy(features).float().unsqueeze(0)  # (1, seq_len, features)
            x = x.to(self.device)
            
            # Run inference
            with torch.no_grad():
                output = self.model(x)
            
            # Get probability
            prob_up = output.item()
            
            # Apply exponential smoothing
            prob_up_smoothed = (
                self.smooth_alpha * prob_up +
                (1 - self.smooth_alpha) * self.last_prob_up
            )
            
            # Update last probability
            self.last_prob_up = prob_up_smoothed
            
            return prob_up, prob_up_smoothed
            
        except Exception as e:
            logger.error(f"Error during inference: {e}")
            return None
    
    def reset_smoothing(self):
        """Reset smoothing state (e.g., after regime change)."""
        self.last_prob_up = 0.5
        logger.debug("Smoothing state reset")
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        if self.model is None:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "input_size": self.model.input_size,
            "hidden_size": self.model.hidden_size,
            "num_layers": self.model.num_layers,
            "device": str(self.device),
            "parameters": sum(p.numel() for p in self.model.parameters()),
        }


def create_dummy_model(save_path: str, input_size: int = 27):
    """
    Create and save a dummy model for testing.
    
    Args:
        save_path: Path to save the model
        input_size: Number of input features
    """
    model = CandleLSTM(input_size=input_size)
    
    # Save model
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': input_size,
    }, save_path)
    
    logger.info(f"Dummy model saved to {save_path}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing ModelInference...")
    
    # Create dummy model
    model_path = "models/current_candle_lstm.pt"
    Path("models").mkdir(exist_ok=True)
    
    print(f"Creating dummy model at {model_path}...")
    create_dummy_model(model_path)
    
    # Test inference
    inference = ModelInference(model_path, smooth_alpha=0.25)
    
    print("Loading model...")
    if inference.load_model(input_size=27):
        print("Model loaded successfully!")
        
        # Get model info
        info = inference.get_model_info()
        print(f"Model info: {info}")
        
        # Test prediction with dummy data
        dummy_features = np.random.randn(64, 27).astype(np.float32)
        
        print("Running inference on dummy data...")
        result = inference.predict(dummy_features)
        
        if result:
            prob_up, prob_up_smoothed = result
            print(f"Prob UP: {prob_up:.4f}")
            print(f"Prob UP (smoothed): {prob_up_smoothed:.4f}")
            print(f"Prob DOWN: {1-prob_up:.4f}")
        else:
            print("Inference failed!")
    else:
        print("Failed to load model!")
