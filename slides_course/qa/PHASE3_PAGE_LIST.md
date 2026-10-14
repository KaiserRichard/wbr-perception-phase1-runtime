1. WBR Perception Implementation
2. Contents
3. Section: Introduction
4. 1.1 Robot context
5. 1.2 Engineering problem
6. 1.3 Objectives
7. 1.4 Research questions
8. Section: Background
9. 2.1 Stereo geometry
10. 2.2 Visual-inertial estimation
11. 2.3 Odometry and mapping
12. 2.4 D435i streams
13. 2.5 ROS communication
14. 2.6 QoS compatibility
15. 2.7 EuRoC baseline
16. Section: System design
17. 3.1 Machine ownership
18. 3.2 Control boundary
19. 3.3 Physical platform
20. 3.4 Sensor-to-pose execution path
21. 3.4 Topic and type contract
22. 3.5 Threads and backpressure
23. 3.6 Queues and backpressure
24. 3.7 Payload budget
25. 3.8 Storage qualification
26. 3.9 Software provenance
27. 3.10 Frame definitions
28. 3.11 Robot transform ownership
29. 3.12 Camera transform ownership
30. 3.13 Independent IMUs
31. 3.14 Transform direction
32. 3.15 Timestamp fields and domains
33. 3.16 Where timestamps are stamped
34. 3.17 Global time
35. 3.18 Worked latency decomposition
36. 3.19 Calibration register
37. 3.20 Stereo calibration
38. 3.21 Calibration capture
39. 3.22 IMU noise
40. 3.23 Calibration tools
41. 3.24 Algorithm threads
42. 3.25 Tracking
43. 3.26 Mapping and Atlas
44. 3.27 Inertial initialization
45. 3.28 Settings audit before tuning
46. 3.28 Numeric IMU settings contract
47. 3.29 Input association
48. 3.30 Planned health envelope
49. 3.31 Health supervision
50. 3.32 Planned Pi-to-STM32 boundary
51. Section: Implementation by gate
52. 4.1 Gate dependencies and status
53. 4.2 N0: platform preflight
54. 4.2 N0: acceptance and diagnosis
55. 4.2 N0: physical inventory record
56. 4.3 N1: own-branch USB and access
57. 4.3 N1: acceptance and diagnosis
58. 4.4 N2: staged native acquisition
59. 4.4 N2: reproduction and mandatory soak
60. 4.5 N2: delivery criteria
61. 4.5 N2: content, health and acceptance
62. 4.5 N2: seal reviewed evidence
63. 4.5 Worked window-rate and boundary check
64. 4.6 N3: one wrapper, bounded record
65. 4.7 N3: stop camera and replay
66. 4.7 N3: PASS/FAIL matrix
67. 4.7 Storage prerequisite: no mount fallback
68. 4.7 Content checks beyond delivery rates
69. 4.8 Stereo extension
70. 4.9 N4A: camera-independent EuRoC baseline
71. 4.9 N4A: estimator acceptance contract
72. 4.10 N4B: offline D435i stereo
73. 4.10 N4B: input and run criteria
74. 4.10 N4B: immutable adapter provenance
75. 4.11 N4C: live stereo scheduling
76. 4.11 N4C: live PASS/FAIL criteria
77. 4.12 N5: reproducible measurement
78. 4.12 N5: measurement criteria
79. 4.13 N6: health semantics with fixtures
80. 4.13 N6: planned acceptance table
81. 4.14 N7: staged controller boundary
82. 4.14 N7: planned acceptance table
83. 4.15 Reproduction and evidence
84. 4.16 Bottom-up diagnosis
85. 4.17 Failure isolation
86. 4.18 Bounded AI tickets
87. Section: Evaluation method
88. 5.1 Experimental design
89. 5.2 ATE computation outline
90. 5.2 Symbolic ATE worked example
91. 5.3 RPE and pair policy
92. 5.4 Trajectory conversion and evo
93. 5.5 Initialization and continuity
94. 5.6 Latency and loss
95. 5.7 Resource measurements
96. 5.8 Accuracy results
97. 5.9 Timing results
98. 5.10 Resource results
99. Section: Engineering decisions
100. 6.1 Runtime and USB
101. 6.2 Inputs and clocks
102. 6.3 Algorithm and calibration
103. 6.4 Interface decisions
104. Section: Current status and roadmap
105. 7.1 Historical evidence
106. 7.2 Current evidence gaps
107. 7.3 Conditional roadmap
108. 8. Conclusion
109. References
