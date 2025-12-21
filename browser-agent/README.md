# APT Browser Agent

Real User Monitoring (RUM) SDK for collecting performance metrics from web browsers.

## Features

- ✅ **Web Vitals**: LCP, FID, CLS, FCP, TTFB
- ✅ **Navigation Timing**: DNS, TCP, Request/Response, DOM processing
- ✅ **Resource Timing**: Track all resource load times
- ✅ **Emit/Serve Modes**: Push to backend or query locally
- ✅ **Lightweight**: < 10KB minified
- ✅ **TypeScript**: Full type definitions

## Installation

### Via NPM

```bash
npm install @apt/browser-agent
```

### Via CDN

```html
<script src="https://cdn.example.com/apt-browser-agent.min.js"></script>
```

### Build from Source

```bash
cd browser-agent
npm install
npm run build
```

Output: `dist/apt-browser-agent.min.js`

## Usage

### Method 1: Auto-Initialize

```html
<script>
  window.APTBrowserAgentConfig = {
    name: 'my-website',
    mode: 'emit',
    emitTarget: 'https://metrics.company.com/browser-metrics',
    authToken: 'your-token',
    sampleRate: 1.0,  // 100% sampling
    debug: true
  };
</script>
<script src="apt-browser-agent.min.js"></script>
```

### Method 2: Manual Initialize

```html
<script src="apt-browser-agent.min.js"></script>
<script>
  const agent = new APTBrowserAgent.APTBrowserAgent({
    name: 'my-website',
    mode: 'serve',  // Store locally
    sampleRate: 0.1,  // 10% sampling
    debug: false
  });
  
  agent.init();
  
  // Query metrics later
  const metrics = agent.getMetrics({ name: 'web_vitals_lcp' });
  console.log('LCP metrics:', metrics);
</script>
```

### Method 3: ES Module

```typescript
import APTBrowserAgent from '@apt/browser-agent';

const agent = new APTBrowserAgent({
  name: 'my-app',
  mode: 'emit',
  emitTarget: 'https://metrics.company.com/browser-metrics'
});

agent.init();
```

## Configuration

```typescript
interface AgentConfig {
  name: string;              // Agent identifier
  mode: 'emit' | 'serve';    // Operating mode
  emitTarget?: string;       // Backend URL (emit mode)
  authToken?: string;        // Authentication token
  sampleRate?: number;       // 0-1 (default: 1.0)
  debug?: boolean;           // Enable logging
}
```

## Collected Metrics

### Web Vitals

- `web_vitals_lcp` - Largest Contentful Paint
- `web_vitals_fid` - First Input Delay
- `web_vitals_cls` - Cumulative Layout Shift
- `web_vitals_fcp` - First Contentful Paint
- `web_vitals_ttfb` - Time to First Byte

### Navigation Timing

- `navigation_dns_lookup` - DNS resolution time
- `navigation_tcp_connection` - TCP connection time
- `navigation_request_time` - Request time
- `navigation_response_time` - Response time
- `navigation_dom_processing` - DOM processing time
- `navigation_dom_content_loaded` - DOMContentLoaded time
- `navigation_page_load` - Full page load time
- `navigation_time_to_first_byte` - TTFB

### Resource Timing

- `resource_load_time` - Individual resource load times
  - Tags: `resource_type`, `resource_name`

## API

### `init()`

Initialize the agent and start collecting metrics.

```typescript
agent.init();
```

### `addMetric(metric)`

Add a custom metric.

```typescript
agent.addMetric({
  name: 'custom_metric',
  value: 123.45,
  unit: 'ms',
  timestamp: Date.now(),
  tags: { custom: 'tag' }
});
```

### `getMetrics(filter?)`

Get collected metrics.

```typescript
// Get all metrics
const all = agent.getMetrics();

// Filter by name
const lcp = agent.getMetrics({ name: 'web_vitals_lcp' });

// Filter by time
const recent = agent.getMetrics({ since: Date.now() - 60000 });
```

### `clearMetrics()`

Clear all collected metrics.

```typescript
agent.clearMetrics();
```

## Integration with APT Framework

### Backend Endpoint

The browser agent can emit metrics to any APT remote agent:

```yaml
# Deploy a browser metrics collector
agents:
  browser-metrics:
    endpoint: "https://metrics.company.com:9090"
    auth_token: "${BROWSER_METRICS_TOKEN}"

workflows:
  process_browser_metrics:
    steps:
      - name: query_browser_metrics
        action: agent_query
        agent: browser-metrics
        metric: "web_vitals_lcp"
        timerange: "last_1h"
```

### Frontend Integration

```html
<script>
  window.APTBrowserAgentConfig = {
    name: 'production-website',
    mode: 'emit',
    emitTarget: 'https://metrics.company.com:9090/browser-metrics',
    authToken: 'your-browser-metrics-token',
    sampleRate: 0.1  // 10% of users
  };
</script>
<script src="/static/apt-browser-agent.min.js"></script>
```

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- IE11: ⚠️  Partial support (no Web Vitals)

## Performance Impact

- **Bundle Size**: ~8KB minified + gzipped
- **CPU Overhead**: <1% on average
- **Memory**: ~100KB for 1000 metrics

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Watch mode
npm run watch

# Development build
npm run dev
```

## License

MIT

## See Also

- [Web Vitals](https://web.dev/vitals/)
- [Navigation Timing API](https://developer.mozilla.org/en-US/docs/Web/API/Navigation_timing_API)
- [Resource Timing API](https://developer.mozilla.org/en-US/docs/Web/API/Resource_Timing_API)
