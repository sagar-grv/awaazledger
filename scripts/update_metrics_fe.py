with open('frontend/src/pages/Metrics.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

if 'ContinuousLearningPanel' not in text:
    text = text.replace(
        "import { fetchMetricsDashboard, fetchLearningMetrics } from '../lib/api';",
        "import { fetchMetricsDashboard, fetchLearningMetrics } from '../lib/api';\nimport { ContinuousLearningPanel } from '../components/ContinuousLearningPanel';"
    )

old_ending = "    </div>\n  );\n};"
new_ending = "      {/* Autonomous Continuous Learning & Self-Improvement Telemetry */}\n      <ContinuousLearningPanel />\n    </div>\n  );\n};"

text = text.replace(old_ending, new_ending)
text = text.replace(old_ending.replace('\n', '\r\n'), new_ending.replace('\n', '\r\n'))

with open('frontend/src/pages/Metrics.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("METRICS_UPDATED")
