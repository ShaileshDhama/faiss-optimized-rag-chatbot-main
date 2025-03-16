from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server
from typing import Optional, Dict, Any
import time
from functools import wraps
from loguru import logger
import json
import psutil
import numpy as np
from datetime import datetime

class TelemetryService:
    def __init__(self, app_name: str = "finance_chatbot"):
        self.app_name = app_name
        self._setup_telemetry()
        self.metrics = {}
        
    def _setup_telemetry(self):
        """Initialize OpenTelemetry components"""
        # Resource for identifying the service
        resource = Resource.create({"service.name": self.app_name})
        
        # Setup tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        self.tracer = trace.get_tracer(__name__)
        
        # Setup metrics
        self.meter_provider = MeterProvider(resource=resource)
        self.meter = self.meter_provider.get_meter(__name__)
        
        # Create metrics
        self._create_metrics()
        
    def _create_metrics(self):
        """Create custom metrics"""
        # Response time histogram
        self.metrics["response_time"] = self.meter.create_histogram(
            name="response_time_seconds",
            description="Response time in seconds",
            unit="s"
        )
        
        # Query counter
        self.metrics["query_counter"] = self.meter.create_counter(
            name="total_queries",
            description="Total number of queries processed"
        )
        
        # Cache hit ratio
        self.metrics["cache_hits"] = self.meter.create_counter(
            name="cache_hits",
            description="Number of cache hits"
        )
        
        # FAISS search latency
        self.metrics["faiss_latency"] = self.meter.create_histogram(
            name="faiss_search_latency",
            description="FAISS search latency in seconds",
            unit="s"
        )
        
        # LLM generation time
        self.metrics["llm_generation_time"] = self.meter.create_histogram(
            name="llm_generation_time",
            description="LLM response generation time in seconds",
            unit="s"
        )
        
        # System metrics
        self.metrics["memory_usage"] = self.meter.create_observable_gauge(
            name="memory_usage_bytes",
            description="Current memory usage in bytes",
            callback=self._get_memory_usage
        )
        
        self.metrics["cpu_usage"] = self.meter.create_observable_gauge(
            name="cpu_usage_percent",
            description="Current CPU usage percentage",
            callback=self._get_cpu_usage
        )

    def instrument_fastapi(self, app):
        """Instrument FastAPI application"""
        FastAPIInstrumentor.instrument_app(app)

    def start_prometheus_server(self, port: int = 9090):
        """Start Prometheus metrics server"""
        try:
            reader = PrometheusMetricReader()
            self.meter_provider.add_metric_reader(reader)
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {str(e)}")

    def track_performance(self, operation: str):
        """Decorator to track operation performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                # Start span for tracing
                with self.tracer.start_as_current_span(operation) as span:
                    try:
                        result = await func(*args, **kwargs)
                        
                        # Record metrics
                        duration = time.time() - start_time
                        self.metrics["response_time"].record(duration)
                        self.metrics["query_counter"].add(1)
                        
                        # Add span attributes
                        span.set_attribute("duration_seconds", duration)
                        span.set_attribute("success", True)
                        
                        return result
                    
                    except Exception as e:
                        # Record error in span
                        span.set_attribute("success", False)
                        span.set_attribute("error", str(e))
                        raise
                        
            return wrapper
        return decorator

    def record_cache_hit(self):
        """Record a cache hit"""
        self.metrics["cache_hits"].add(1)

    def record_faiss_latency(self, duration: float):
        """Record FAISS search latency"""
        self.metrics["faiss_latency"].record(duration)

    def record_llm_generation_time(self, duration: float):
        """Record LLM generation time"""
        self.metrics["llm_generation_time"].record(duration)

    def _get_memory_usage(self):
        """Get current memory usage"""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return 0

    def _get_cpu_usage(self):
        """Get current CPU usage"""
        try:
            return psutil.cpu_percent()
        except Exception as e:
            logger.error(f"Error getting CPU usage: {str(e)}")
            return 0

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            # Collect system metrics
            memory = psutil.virtual_memory()
            cpu_times = psutil.cpu_times_percent()
            
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_metrics": {
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used
                    },
                    "cpu": {
                        "user": cpu_times.user,
                        "system": cpu_times.system,
                        "idle": cpu_times.idle
                    }
                },
                "application_metrics": {
                    "process_memory": self._get_memory_usage(),
                    "process_cpu": self._get_cpu_usage()
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {"error": str(e)}
