# Performance Testing Framework Architecture

## Overview

This document describes the architecture of the Neuron Performance Testing Framework.

## Components

### Core Framework (`src/core/`)

- **base_performance_tester.py** - Base classes and configuration
- **ui_performance_tester.py** - UI testing with Playwright
- **api_performance_tester.py** - API testing with aiohttp
- **metrics_collector.py** - Metrics aggregation and analysis
- **report_generator.py** - HTML/JSON report generation
- **test_definition_loader.py** - YAML test definition loader
- **pytest_fixtures.py** - Pytest integration

### Test Layer (`tests/`)

- **definitions/** - YAML-based test definitions
- **ui/** - Python UI performance tests
- **api/** - Python API performance tests
- **pytest_perf_plugin.py** - Pytest plugin for YAML tests

### Configuration (`config/`)

- **performance_config.yml** - Performance test configuration

## Data Flow

```
YAML Test Definition
        ↓
PerformanceTestDefinition (loader)
        ↓
PerformanceTestRunner
        ↓
    ┌───────┴───────┐
    ↓               ↓
UIPerformanceTester  APIPerformanceTester
    ↓               ↓
MetricsCollector
    ↓
ReportGenerator
    ↓
HTML + JSON Reports
```

## Metrics Collection

### UI Metrics
- Navigation timing
- Resource timing
- Paint metrics
- Core Web Vitals
- Memory usage
- Network requests

### API Metrics
- Request/response timing
- Throughput
- Concurrent performance
- Error rates

## Reporting

Reports include:
- Executive summary
- Detailed test results
- Statistical analysis (P50, P75, P90, P95, P99)
- Percentile charts
- Configuration details
