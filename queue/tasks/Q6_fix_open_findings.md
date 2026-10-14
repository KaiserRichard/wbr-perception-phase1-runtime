# Q6 — fix the OPEN findings of tools/REVIEW_Q4.md
Read queue/tasks/COMMON_QUEUE.md first (rules). Read tools/REVIEW_Q4.md. For every finding marked OPEN
(Python ROS gate NaN clock evidence; ROS skeleton pause/forward-seek rules; harness missing declared artifact;
harness descendant processes after a trial; optional ORB IMU double->float narrowing guard): add a failing test,
fix it minimally, make it pass, and update that finding to FIXED with evidence (or NOT-A-BUG with reasoning).
Code that cannot be compiled here (ROS skeleton, ORB binding) gets the fix plus a ROS-free/ORB-free test of the
same logic where possible; otherwise mark OPEN-UNBUILDABLE. Edit only under tools/. Rerun every suite listed in
REVIEW_Q4.md "Validation commands" and update that table. Write no new REPORT file; update REVIEW_Q4.md only.
