# Reader self-review — first rendered draft

Reviewed all 45 page images in order at 1280 × 719, imagining a fourth-year electronics student new to vision and SLAM. This is an author self-review, not an independent student study. The questions were: can I explain this aloud after one reading, are terms defined before use, and does the page teach rather than report to another agent?

Pages 1–3, 5–6, 10, 12–13, 15, 21, 24, 26, 31, 33–34, 36–39, and 41–43 were understandable on this pass. Pages 6 and 13 could use more breathing room. Specific issues follow.

| Page | Exact wording or visual that lost me | What I needed |
|---|---|---|
| 4 | “Planned checked interface” overlaps both boxes. | Put the connection label above the boxes so I can read the controller boundary. |
| 7 | “Illustrative rectified images” and “focal length” | Explain that rectification aligns matching image rows, and that focal length here sets projection scale in pixels. |
| 8 | The dashed line under “Offset plus scatter” | Identify it as the unbiased reference; otherwise I cannot distinguish bias from signal level. |
| 9 | “features” in the title; “image correspondence” | Give features a short definition here, and say “matching points” instead of introducing another term. |
| 11 | “two axes per frame” but only one red camera arrow | Show both camera axes and explicitly identify the robot drawing as schematic. |
| 14 | “does not give latency” | Use “time delay” because latency has not been introduced yet. |
| 16 | “mapped points” | Say previously estimated scene points before the map-point definition on the next page. |
| 17 | “an image pose kept” | A keyframe keeps an image and its pose; make that explicit. |
| 18 | “metric scale” | Say that stereo provides distances in metres rather than arbitrary units. |
| 19 | “ORB-SLAM3 separates” and “Nearby ge-ometry” | Identify ORB-SLAM3 as the chosen SLAM software and remove the awkward diagram hyphenation. |
| 20 | “Wrong calibration” | Define calibration before listing why a wrong one breaks tracking. |
| 22 | “Stereo geometry” and “Rigid relation” overlap boxes. | Move relation labels above the diagram. |
| 23 | “Conceptual fixed target; this artwork is not a usable calibration grid.” | Shorten this caption and leave space between image and explanation. |
| 25, 28 | “SDK adapter” | Define SDK beside librealsense before the recap uses it. |
| 27 | “The current D435i adapter” and the takeaway at the footer | Clarify adapter means the input program; reduce the oversized illustration and caption. |
| 29 | “Compare same time” overlaps the pose boxes; “table-camera take” | Raise the label; say table-camera recording. |
| 30 | Colored trajectories with no legend | Say which color is the reference and which is the estimate. |
| 32 | Crowded lower paragraphs; the enlarged “1 cm difference” drawing | Reduce vertical diagram extent, label the drawing not to scale, and keep the actual example numerical. |
| 35 | “300-second soak” and “raw samples” | Explain this is five minutes of continuous sensor delivery, before middleware. |
| 40 | “stereo take” and “gates remain unqualified” | Use recording, and say no gate has been accepted for the current setup. |
| 44 | Swift command appears as three separate commands. | Add shell continuation characters so the printed command is runnable. |

No evidence keys, hashes, file paths or command flags appear on the teaching pages. The current-state page is the only page carrying the project's overall qualification status. Some first-draft phrases (“take,” “unqualified,” “SDK adapter”) still sounded like a technical handoff; the substitutions above address them.

The five most important fixes:

1. Define rectification, focal length, features, metric scale and calibration at their first use.
2. Remove all arrow-label collisions and give the bag and RPE pages enough room above the footer.
3. Clearly distinguish the ROS recording route from the direct SDK input program without unexplained abbreviations.
4. Make the example drawings interpretable: identify the noise baseline, both frame axes, trajectory colors and schematic RPE scale.
5. Replace handoff wording and correct the appendix command continuations.

These fixes will be applied to the source, followed by a complete rebuild, render and inspection of the final images. Final results are recorded in REVIEW_LOG.md.

## Revisions and second reader pass

Applied all five priority fixes, regenerated the source, rebuilt and rendered again. Read all 45 revised page images in order. The diagrams are readable, the bag and RPE takeaways clear the footer, and the Swift command now has continuation characters. Pages 23 and 30 received one further wording refinement: describe a camera–IMU offset as a shift between timelines, and use “distances in metres” instead of “metric scale.” Those pages were rebuilt and their final images were rechecked separately; both are clear and fit. The review remains a self-review, not a claim of independent student validation.
