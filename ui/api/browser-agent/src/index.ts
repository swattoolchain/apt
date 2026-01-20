/**
 * APT Browser Agent - Main Entry Point
 * 
 * Collects Real User Monitoring (RUM) data including:
 * - Navigation Timing
 * - Resource Timing
 * - Web Vitals (LCP, FID, CLS, FCP, TTFB)
 */

import { onCLS, onFID, onLCP, onFCP, onTTFB, Metric } from 'web-vitals';

export interface AgentConfig {
    /** Agent name/identifier */
    name: string;

    /** Operating mode */
    mode: 'emit' | 'serve';

    /** Endpoint URL for emit mode */
    emitTarget?: string;

    /** Authentication token */
    authToken?: string;

    /** Sample rate (0-1, default: 1.0 = 100%) */
    sampleRate?: number;

    /** Enable debug logging */
    debug?: boolean;
}

export interface PerformanceMetric {
    /** Metric name */
    name: string;

    /** Metric value */
    value: number;

    /** Metric unit */
    unit: string;

    /** Timestamp */
    timestamp: number;

    /** Additional tags */
    tags?: Record<string, string>;
}

export class APTBrowserAgent {
    private config: AgentConfig;
    private metrics: PerformanceMetric[] = [];
    private initialized = false;

    constructor(config: AgentConfig) {
        this.config = {
            sampleRate: 1.0,
            debug: false,
            ...config
        };
    }

    /**
     * Initialize the agent and start collecting metrics
     */
    public init(): void {
        if (this.initialized) {
            this.log('Agent already initialized');
            return;
        }

        // Check sampling
        if (Math.random() > (this.config.sampleRate || 1.0)) {
            this.log('Skipped due to sampling');
            return;
        }

        this.log('Initializing APT Browser Agent');

        // Collect Web Vitals
        this.setupWebVitals();

        // Collect Navigation Timing
        this.collectNavigationTiming();

        // Collect Resource Timing
        this.collectResourceTiming();

        this.initialized = true;
    }

    /**
     * Setup Web Vitals collection
     */
    private setupWebVitals(): void {
        onCLS((metric) => this.recordWebVital(metric));
        onFID((metric) => this.recordWebVital(metric));
        onLCP((metric) => this.recordWebVital(metric));
        onFCP((metric) => this.recordWebVital(metric));
        onTTFB((metric) => this.recordWebVital(metric));
    }

    /**
     * Record a Web Vital metric
     */
    private recordWebVital(metric: Metric): void {
        this.addMetric({
            name: `web_vitals_${metric.name.toLowerCase()}`,
            value: metric.value,
            unit: 'ms',
            timestamp: Date.now(),
            tags: {
                rating: metric.rating,
                navigationType: metric.navigationType
            }
        });

        this.log(`Web Vital: ${metric.name} = ${metric.value}`);
    }

    /**
     * Collect Navigation Timing metrics
     */
    private collectNavigationTiming(): void {
        if (!window.performance || !window.performance.timing) {
            this.log('Navigation Timing API not supported');
            return;
        }

        // Wait for page load
        window.addEventListener('load', () => {
            setTimeout(() => {
                const timing = window.performance.timing;
                const navigationStart = timing.navigationStart;

                const metrics = {
                    dns_lookup: timing.domainLookupEnd - timing.domainLookupStart,
                    tcp_connection: timing.connectEnd - timing.connectStart,
                    request_time: timing.responseStart - timing.requestStart,
                    response_time: timing.responseEnd - timing.responseStart,
                    dom_processing: timing.domComplete - timing.domLoading,
                    dom_content_loaded: timing.domContentLoadedEventEnd - navigationStart,
                    page_load: timing.loadEventEnd - navigationStart,
                    time_to_first_byte: timing.responseStart - navigationStart
                };

                Object.entries(metrics).forEach(([name, value]) => {
                    if (value >= 0) {
                        this.addMetric({
                            name: `navigation_${name}`,
                            value,
                            unit: 'ms',
                            timestamp: Date.now()
                        });
                    }
                });

                this.log('Navigation Timing collected');
            }, 0);
        });
    }

    /**
     * Collect Resource Timing metrics
     */
    private collectResourceTiming(): void {
        if (!window.performance || !window.performance.getEntriesByType) {
            this.log('Resource Timing API not supported');
            return;
        }

        window.addEventListener('load', () => {
            setTimeout(() => {
                const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[];

                resources.forEach((resource) => {
                    this.addMetric({
                        name: 'resource_load_time',
                        value: resource.duration,
                        unit: 'ms',
                        timestamp: Date.now(),
                        tags: {
                            resource_type: resource.initiatorType,
                            resource_name: resource.name.split('/').pop() || 'unknown'
                        }
                    });
                });

                this.log(`Collected ${resources.length} resource timings`);
            }, 0);
        });
    }

    /**
     * Add a custom metric
     */
    public addMetric(metric: PerformanceMetric): void {
        this.metrics.push(metric);

        // Emit immediately if in emit mode
        if (this.config.mode === 'emit' && this.config.emitTarget) {
            this.emitMetric(metric);
        }
    }

    /**
     * Emit metric to backend
     */
    private async emitMetric(metric: PerformanceMetric): Promise<void> {
        if (!this.config.emitTarget) return;

        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            };

            if (this.config.authToken) {
                headers['Authorization'] = `Bearer ${this.config.authToken}`;
            }

            await fetch(this.config.emitTarget, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    agent_name: this.config.name,
                    metrics: [metric]
                })
            });
        } catch (error) {
            this.log(`Failed to emit metric: ${error}`);
        }
    }

    /**
     * Get all collected metrics
     */
    public getMetrics(filter?: { name?: string; since?: number }): PerformanceMetric[] {
        let filtered = this.metrics;

        if (filter?.name) {
            filtered = filtered.filter(m => m.name === filter.name);
        }

        if (filter?.since) {
            filtered = filtered.filter(m => m.timestamp >= filter.since);
        }

        return filtered;
    }

    /**
     * Clear all metrics
     */
    public clearMetrics(): void {
        this.metrics = [];
    }

    /**
     * Log debug message
     */
    private log(message: string): void {
        if (this.config.debug) {
            console.log(`[APT Browser Agent] ${message}`);
        }
    }
}

// Auto-initialize if config is in window
declare global {
    interface Window {
        APTBrowserAgentConfig?: AgentConfig;
    }
}

if (typeof window !== 'undefined' && window.APTBrowserAgentConfig) {
    const agent = new APTBrowserAgent(window.APTBrowserAgentConfig);
    agent.init();
}

export default APTBrowserAgent;
