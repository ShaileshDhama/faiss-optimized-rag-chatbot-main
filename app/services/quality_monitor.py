from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from ydata_profiling import ProfileReport
import json
from loguru import logger
import tiktoken
from collections import defaultdict

class QualityMonitorService:
    def __init__(self):
        self.response_metrics = defaultdict(list)
        self.query_metrics = defaultdict(list)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    async def analyze_response_quality(
        self,
        query: str,
        response: str,
        context: List[str],
        response_time: float
    ) -> Dict:
        """Analyze the quality of a chatbot response"""
        try:
            # Token analysis
            query_tokens = self.tokenizer.encode(query)
            response_tokens = self.tokenizer.encode(response)
            
            # Calculate metrics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "response_length": len(response),
                "query_length": len(query),
                "response_tokens": len(response_tokens),
                "query_tokens": len(query_tokens),
                "response_time": response_time,
                "context_relevance": self._calculate_context_relevance(query, context),
                "response_coherence": self._analyze_coherence(response),
                "factual_consistency": self._check_factual_consistency(response, context)
            }
            
            # Store metrics for trending
            self._update_metrics(metrics)
            
            # Add quality score
            metrics["quality_score"] = self._calculate_quality_score(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing response quality: {str(e)}")
            return {"error": str(e)}

    def _calculate_context_relevance(self, query: str, context: List[str]) -> float:
        """Calculate relevance of retrieved context to query"""
        try:
            if not context:
                return 0.0
                
            # Simple keyword matching for demonstration
            query_words = set(query.lower().split())
            
            relevance_scores = []
            for ctx in context:
                ctx_words = set(ctx.lower().split())
                overlap = len(query_words.intersection(ctx_words))
                score = overlap / len(query_words) if query_words else 0
                relevance_scores.append(score)
            
            return sum(relevance_scores) / len(relevance_scores)
            
        except Exception:
            return 0.0

    def _analyze_coherence(self, text: str) -> float:
        """Analyze text coherence using basic metrics"""
        try:
            sentences = text.split('.')
            if len(sentences) <= 1:
                return 1.0
                
            # Calculate sentence length variance (lower is better)
            lengths = [len(s.strip().split()) for s in sentences if s.strip()]
            length_variance = np.var(lengths) if lengths else 0
            
            # Normalize to 0-1 scale (inverse, as lower variance is better)
            coherence_score = 1 / (1 + length_variance)
            
            return coherence_score
            
        except Exception:
            return 0.0

    def _check_factual_consistency(self, response: str, context: List[str]) -> float:
        """Check factual consistency between response and context"""
        try:
            if not context:
                return 0.0
                
            # Simple approach: check if key phrases from context appear in response
            consistency_scores = []
            
            for ctx in context:
                # Extract key phrases (simple approach using nouns)
                ctx_words = set(ctx.lower().split())
                response_words = set(response.lower().split())
                
                # Calculate word overlap
                overlap = len(ctx_words.intersection(response_words))
                score = overlap / len(ctx_words) if ctx_words else 0
                consistency_scores.append(score)
            
            return sum(consistency_scores) / len(consistency_scores)
            
        except Exception:
            return 0.0

    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate overall quality score"""
        try:
            weights = {
                "context_relevance": 0.3,
                "response_coherence": 0.3,
                "factual_consistency": 0.4
            }
            
            score = sum(
                metrics[metric] * weight
                for metric, weight in weights.items()
            )
            
            return round(score, 3)
            
        except Exception:
            return 0.0

    def _update_metrics(self, metrics: Dict):
        """Update stored metrics for trending analysis"""
        timestamp = datetime.utcnow()
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                self.response_metrics[key].append((timestamp, value))
        
        # Keep only last 24 hours of data
        cutoff = timestamp - timedelta(hours=24)
        for key in self.response_metrics:
            self.response_metrics[key] = [
                (ts, val) for ts, val in self.response_metrics[key]
                if ts > cutoff
            ]

    async def generate_quality_report(self) -> Dict:
        """Generate comprehensive quality report"""
        try:
            current_time = datetime.utcnow()
            report = {
                "timestamp": current_time.isoformat(),
                "metrics_summary": {},
                "trends": {},
                "alerts": []
            }
            
            # Calculate metrics summary
            for metric, values in self.response_metrics.items():
                if values:
                    recent_values = [v for t, v in values if t > current_time - timedelta(hours=1)]
                    if recent_values:
                        report["metrics_summary"][metric] = {
                            "mean": np.mean(recent_values),
                            "std": np.std(recent_values),
                            "min": min(recent_values),
                            "max": max(recent_values)
                        }
            
            # Calculate trends
            for metric, values in self.response_metrics.items():
                if len(values) >= 2:
                    times, metrics = zip(*values)
                    trend = np.polyfit(
                        [(t - current_time).total_seconds() for t in times],
                        metrics,
                        deg=1
                    )[0]
                    report["trends"][metric] = {
                        "direction": "increasing" if trend > 0 else "decreasing",
                        "magnitude": abs(trend)
                    }
            
            # Generate alerts
            if report["metrics_summary"].get("quality_score", {}).get("mean", 1) < 0.5:
                report["alerts"].append({
                    "level": "warning",
                    "message": "Average response quality score is below threshold"
                })
            
            if report["metrics_summary"].get("response_time", {}).get("mean", 0) > 5:
                report["alerts"].append({
                    "level": "warning",
                    "message": "Average response time is above 5 seconds"
                })
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating quality report: {str(e)}")
            return {"error": str(e)}

    async def analyze_data_distribution(self, data: List[Dict]) -> Dict:
        """Analyze data distribution and generate profile report"""
        try:
            df = pd.DataFrame(data)
            profile = ProfileReport(
                df,
                title="Data Quality Report",
                minimal=True
            )
            
            # Extract key statistics
            stats = {
                "row_count": len(df),
                "missing_values": df.isnull().sum().to_dict(),
                "correlation_matrix": df.corr().to_dict() if df.select_dtypes(include=[np.number]).columns.any() else {},
                "basic_stats": df.describe().to_dict()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing data distribution: {str(e)}")
            return {"error": str(e)}
