Agentic Software Engineering: Robot Navigation Project

Group: Crowley's & Sprite  
Repository: https://github.com/njitWangZhihao/scse_agentic_se_Crowley-s-Sprite

1. Project Overview

This project implements an AI-based multi-agent software engineering process for mobile robot navigation tasks.

The system uses Ollama to call the Qwen3:8b large language model to complete software requirement analysis, formulate implementation plans, generate navigation logic, create automated tests, evaluate simulation performance, review results, and modify code as necessary.

The main navigation functions are: `decide_next_move(state)` This function receives obstacle information and the target direction, and returns one of four actions: forward, left turn, right turn, or stop. When the robot encounters an obstruction, it will actively avoid the blocked direction according to the program, in order to move safely towards the target. When the robot cannot detect a safe direction, it will stop at the current position.

2. Multi-Agent Workflow

Requirement analysis: analyst_agent.py → artifacts/requirements.json
Plan formulation:     planner_agent.py → artifacts/plan.json
Code generation:      developer_agent.py → generated/navigation_logic.py
Automatic testing:    test_agent.py → artifacts/test_agent_generated.py
Basic simulation:     runner.py → artifacts/simulation_report.json
Simulation review:    reviewer_agent.py → artifacts/review_report.json
IR-SIM benchmark:     benchmark_irsim.py → four environments
Benchmark review:     reviewer_benchmark_agent.py → artifacts/benchmark_review_report.json
Code revision:        developer_agent.py → generated/navigation_logic_revised.py

3. Technologies Used

Python 3.11、Ollama、Qwen3:8b、pytest、IR-SIM、NumPy、Matplotlib、PyYAML

4. Installation and Environment Setup

git clone https://github.com/njitWangZhihao/scse_agentic_se_Crowley-s-Sprite.git
cd scse_agentic_se_Crowley-s-Sprite
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen3:8b
ollama list

5. Experimental Results

The following results were obtained from the validated navigation implementation.

5.1 Automated Unit Testing

| Metric | Result |
| --- | --- |
| Total pytest tests | 68 |
| Passed tests | 68 |
| Failed tests | 0 |
| Pass rate | 100% |

5.2 Basic Simulation

| Metric | Result |
| --- | --- |
| Total scenarios | 64 |
| Passed scenarios | 64 |
| Failed scenarios | 0 |
| Success rate | 100% |

5.3 IR-SIM Benchmark

The navigation logic was evaluated in four simulation environments.

| Environment | Goal Reached | Steps Taken | Efficiency |
| --- | --- | ---: | --- |
| Easy | Yes | 150 | Efficient |
| Medium | Yes | 148 | Efficient |
| Hard | Yes | 187 | Efficient |
| Custom | Yes | 193 | Efficient |

5.4 Benchmark Summary

| Metric | Result |
| --- | --- |
| Total worlds | 4 |
| Goals reached | 4 |
| Goal completion rate | 100% |
| Efficient worlds | 4 |
| Efficiency rate | 100% |
| Average steps taken | 169.5 |
| Maximum steps allowed | 300 |
| Efficient step limit | 200 |

All four worlds were completed successfully and within the efficient step limit.

5.5 Benchmark Review Results

| Quality Check | Result |
| --- | --- |
| Safety passed | True |
| Goal completion passed | True |
| Efficiency passed | True |
| Needs revision | False |

The Benchmark Reviewer reported no remaining issues based on the recorded benchmark results.

These results describe the validated implementation. Running the AI generation stages again may produce different navigation code and therefore different results.
