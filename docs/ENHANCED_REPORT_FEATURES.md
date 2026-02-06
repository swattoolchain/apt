# Enhanced Report Features - Min/Max & Individual Request Breakdown

## ✅ What Was Added

### **1. Min and Max Response Times**

The detailed metrics view now includes:
- **Min Time** (green badge) - Fastest request
- **Max Time** (red badge) - Slowest request

**Before:**
```
Detailed Metrics:
  - Total Iterations
  - P95
  - P99
  - Throughput
  - Std Dev
  - Median
```

**After:**
```
Detailed Metrics (4-column grid):
  - Total Iterations
  - Min Time (green)  ← NEW
  - Max Time (red)    ← NEW
  - Avg Time          ← NEW
  - Median
  - P95
  - P99
  - Std Dev
  - Throughput (blue)
  - Success Rate      ← NEW
```

### **2. Individual Request Breakdown**

A new collapsible section showing **every single request**:

```
📋 View Individual Request Results (12 requests)
┌─────┬──────────┬────────┬─────────┐
│  #  │ Duration │ Status │ Details │
├─────┼──────────┼────────┼─────────┤
│  1  │  0.043s  │   ✓    │ HTTP 200│
│  2  │  0.045s  │   ✓    │ HTTP 200│
│  3  │  0.042s  │   ✓    │ HTTP 200│
│  4  │  0.047s  │   ✓    │ HTTP 200│
│  5  │  0.044s  │   ✓    │ HTTP 200│
│  6  │  0.053s  │   ✓    │ HTTP 200│
│  7  │  0.041s  │   ✓    │ HTTP 200│
│  8  │  0.046s  │   ✓    │ HTTP 200│
│  9  │  0.048s  │   ✓    │ HTTP 200│
│ 10  │  0.045s  │   ✓    │ HTTP 200│
│ 11  │  0.043s  │   ✓    │ HTTP 200│
│ 12  │  0.044s  │   ✓    │ HTTP 200│
└─────┴──────────┴────────┴─────────┘
```

**Features:**
- ✅ Shows **every single request** (thread × iteration × workflow)
- ✅ Request number (#)
- ✅ Individual duration for each request
- ✅ Success/Fail status (✓ or ✗)
- ✅ HTTP status code or execution status
- ✅ Failed requests highlighted in red background
- ✅ Scrollable table (max-height: 300px)
- ✅ Sticky header for easy navigation

## How It Looks in the Report

### **Step Summary Table**

```
┌──────────────────────┬─────────┬───────┬──────────┬──────────┬─────────┬─────────┐
│ Step                 │ Threads │ Loops │ Total Req│ Avg Time │ Success │ Details │
├──────────────────────┼─────────┼───────┼──────────┼──────────┼─────────┼─────────┤
│ single_thread_test   │    1    │  1x2  │    2     │  0.088s  │  100.0% │    —    │
│ five_thread_test     │    5    │  1x2  │   10     │  0.078s  │  100.0% │ 📋 Stats│
│ multi_iteration_test │    3    │  2x2  │   12     │  0.045s  │  100.0% │ 📋 Stats│
└──────────────────────┴─────────┴───────┴──────────┴──────────┴─────────┴─────────┘
```

### **Click "📋 Stats" to Expand**

```
┌─────────────────────────────────────────────────────────────────────┐
│ Detailed Metrics: five_thread_test                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐     │
│ │Total Iterations│  Min Time   │  Max Time    │  Avg Time    │     │
│ │      10        │  0.043s ✓   │  0.135s ✗    │  0.078s      │     │
│ └──────────────┴──────────────┴──────────────┴──────────────┘     │
│                                                                     │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐     │
│ │   Median     │     P95      │     P99      │   Std Dev    │     │
│ │   0.045s     │   0.135s     │   0.135s     │   0.044s     │     │
│ └──────────────┴──────────────┴──────────────┴──────────────┘     │
│                                                                     │
│ ┌──────────────┬──────────────┐                                    │
│ │  Throughput  │ Success Rate │                                    │
│ │ 12.80 req/s  │   100.0%     │                                    │
│ └──────────────┴──────────────┘                                    │
│                                                                     │
│ ▼ 📋 View Individual Request Results (10 requests)                 │
│   ┌─────┬──────────┬────────┬─────────┐                           │
│   │  #  │ Duration │ Status │ Details │                           │
│   ├─────┼──────────┼────────┼─────────┤                           │
│   │  1  │  0.080s  │   ✓    │ HTTP 200│                           │
│   │  2  │  0.043s  │   ✓    │ HTTP 200│                           │
│   │  3  │  0.045s  │   ✓    │ HTTP 200│                           │
│   │  4  │  0.135s  │   ✓    │ HTTP 200│                           │
│   │  5  │  0.046s  │   ✓    │ HTTP 200│                           │
│   │  6  │  0.077s  │   ✓    │ HTTP 200│                           │
│   │  7  │  0.043s  │   ✓    │ HTTP 200│                           │
│   │  8  │  0.134s  │   ✓    │ HTTP 200│                           │
│   │  9  │  0.045s  │   ✓    │ HTTP 200│                           │
│   │ 10  │  0.133s  │   ✓    │ HTTP 200│                           │
│   └─────┴──────────┴────────┴─────────┘                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Works for ALL Action Types

This feature works for:
- ✅ **api_call** - Shows HTTP status codes
- ✅ **agent_execute** - Shows execution status
- ✅ **k6_test** - Shows test results
- ✅ **jmeter_test** - Shows test results
- ✅ **Any custom action** - Shows generic status

## Example: Failed Request Highlighting

If a request fails:

```
┌─────┬──────────┬────────┬─────────┐
│  #  │ Duration │ Status │ Details │
├─────┼──────────┼────────┼─────────┤
│  1  │  0.043s  │   ✓    │ HTTP 200│
│  2  │  0.045s  │   ✓    │ HTTP 200│
│  3  │  2.500s  │   ✗    │ HTTP 500│  ← Red background
│  4  │  0.047s  │   ✓    │ HTTP 200│
└─────┴──────────┴────────┴─────────┘
```

## Benefits

### **1. Debugging**
- Quickly identify which specific request failed
- See exact duration of each request
- Spot outliers immediately

### **2. Performance Analysis**
- Compare min vs max to see variance
- Identify if certain threads are slower
- Detect patterns in request timing

### **3. Validation**
- Verify all threads executed
- Confirm correct number of requests
- Check HTTP status codes

### **4. Transparency**
- Complete visibility into every request
- No hidden data
- Full audit trail

## Technical Details

### **Data Source**
The individual requests are pulled from `workflow.workflow_executions[].steps[].iteration_results[]`

### **Display Logic**
```jinja2
{% for result in iteration_results %}
  <tr style="{% if not result.success %}background: #fef2f2;{% endif %}">
    <td>{{ loop.index }}</td>
    <td>{{ "%.3f"|format(result.duration) }}s</td>
    <td>
      {% if result.success %}✓{% else %}✗{% endif %}
    </td>
    <td>
      {% if result.data.status_code %}
        HTTP {{ result.data.status_code }}
      {% elif result.data.status %}
        {{ result.data.status }}
      {% endif %}
    </td>
  </tr>
{% endfor %}
```

### **Scrollable Container**
```css
max-height: 300px;
overflow-y: auto;
```

### **Sticky Header**
```css
position: sticky;
top: 0;
background: #f7fafc;
z-index: 1;
```

## Summary

### **Enhanced Metrics:**
1. ✅ Min Time (green badge)
2. ✅ Max Time (red badge)
3. ✅ Avg Time
4. ✅ Success Rate in metrics grid

### **New Feature:**
5. ✅ Individual Request Breakdown Table
   - Request number
   - Duration
   - Status (✓/✗)
   - Details (HTTP code or status)
   - Failed requests highlighted
   - Scrollable with sticky header

### **Applies To:**
- ✅ api_call
- ✅ agent_execute
- ✅ k6_test
- ✅ jmeter_test
- ✅ Any action with multiple iterations

**Now you have complete visibility into every single request!** 🎉
