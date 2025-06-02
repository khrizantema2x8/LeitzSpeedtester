# Leica-Style Persistence-of-Vision Shutter Speed Tester

## Summary

This repository hosts a Python/Pygame application that emulates the classic Leica M3 “drum test” for focal-plane shutter speed calibration. Instead of using complex mechanical shutters with cut-out slits, this digital version leverages persistence of vision on a computer monitor. By displaying a narrow, moving light strip (or multiple strips) at precisely controlled rates (pixels per frame), photographers can visually inspect how their camera’s shutter interacts with varying speeds—just as Leica technicians did decades ago.

## Introduction

Mechanical shutter calibration traditionally required specialized devices: a rotating drum or disk with slits cut at known intervals, illuminated by a lamp, and viewed through a camera. As the shutter curtain traveled behind the slits, sequential bands of light formed on the film, revealing the actual exposure times and curtain tension. This analog method worked beautifully because the human eye’s persistence of vision seamlessly fused those slits into a continuous pattern, making it easy to spot timing errors.

In modern times, finding or maintaining such mechanical testers is all but impossible. However, most computers and external monitors (and soon, web browsers on smartphones) can recreate the same effect digitally—provided the refresh rate is high enough and we account for it precisely. Using Pygame to draw a single (or multiple) narrow white bar(s) moving downward on a black background at user-defined speeds (pixels per frame), we can emulate the classic drum-cut test. The photographer simply sets their camera to bulb mode (or a very long exposure) and points it at the screen. The resulting frame captures the same diagonal-stripe patterns seen in Leica’s original technique.

This project’s goals are:

1. **Reproduce Leica’s drum-cut slit test digitally**
   • Allow a user to scroll one or multiple narrow bars across a “Shutter Test Area” at a known pixel/frame speed.
   • Use persistence of vision to generate a static image in-camera that reveals shutter timing.

2. **Offer a lightweight, cross-platform Pygame implementation**
   • Easy installation via Python 3 and `pip install pygame`.
   • Minimal dependencies—no specialized hardware beyond a reasonably fast computer monitor.

3. **Account for monitor refresh rate limitations**
   • Read and round the display’s refresh rate (e.g., 59.94 Hz → 60 Hz).
   • Display a table of recommended “pixels/frame” values for common refresh rates (60, 75, 120, 144, 240).
   • Warn the user if they exceed the monitor’s safe pixels/frame, because higher values can’t render properly.

4. **Include dual modes**
   • **Single-Beam Mode**: One narrow band traverses the entire test area.
   • **Multibeam Mode**: Five evenly spaced bands cycle together, offering a denser pattern for prolonged exposures (toggle with the **M** key).

5. **Provide an epilepsy warning and help overlay**
   • At first launch, show a mandatory 15-second, check-to-continue epilepsy warning.
   • Include a help overlay (toggle with **H**) that loads “Figure 19.1” from disk (if present) or generates it procedurally, along with explanatory text from the Leica M3 Service Manual.

By packaging all of these features into a single Pygame application, this repository aims to give photographers—especially Leica enthusiasts—a modern, software-only way to verify and fine-tune their camera’s focal-plane shutter without needing vintage mechanical testers.

## Description

### Key Features

1. **Epilepsy Warning Screen**

   * Upon first run, displays a full-screen modal warning.
   * Requires the user to check a box (“I acknowledge the risks and wish to continue”) and then wait a visible 15-second countdown before a “Continue” button becomes enabled.
   * Once acknowledged, the main application appears.

2. **Main Simulation Window**

   * **Shutter Test Area (left)**: A large, outlined rectangle where one or multiple 10-pixel-high white bars scroll continuously from top to bottom, simulating the slit moving across film.
   * **Control Panel (right)**: Fixed 320 px width containing:

     * Title (“Leica Speedtest”)
     * **Controls & About** text (scrolls if needed)
     * Real-time status (“Current Speed: X px/frame,” “Strip Status: Active/Stopped,” “Mode: Dark/Light,” “Beam Mode: Single/Multibeam”)
     * A two-column “Recommended Speeds” table mapping common refresh rates to equal pixels/frame (e.g., 60 Hz → 60 px/frame).
     * One unified **Start/Stop** button at the bottom.

3. **Speed Adjustment**

   * **UP** / **DOWN** arrows adjust the scrolling speed (pixels per frame).
   * Holding **UP**/**DOWN** continuously changes the speed every 200 ms.
   * **Ctrl + UP** / **Ctrl + DOWN** adjust by 5 px/frame at a time.
   * Maximum speed is capped at 200 px/frame. Minimum is 1 px/frame.

4. **Monitor Refresh Rate Awareness**

   * On startup, queries the desktop display mode for its raw refresh rate (e.g., 59.94 Hz), then rounds to the nearest integer (e.g., 60).
   * Displays a table of “Recommended Speeds” (px/frame) for 60 Hz, 75 Hz, 120 Hz, 144 Hz, and 240 Hz.
   * If the user’s chosen speed exceeds the recommended maximum for their rounded refresh rate, a “Speed Warning” popup appears:

     ```
     ┌──────────────────────────────────────────────────────────────┐
     │ Speed Warning                                                │
     │ You have exceeded the recommended speed                       │
     │ Max for 60Hz is 60 px/frame                                   │
     │                                                               │
     │ Speed too fast for effective testing. The refresh rate cannot │
     │ adapt to refresh revolving lines. This leads to still lines   │
     │ on the screen that will not register an image usable for     │
     │ speed testing. Continue at your own risk.                     │
     │                                                               │
     │                  [     Ignore     ]                           │
     └──────────────────────────────────────────────────────────────┘
     ```
   * The popup dims the background to \~80% opacity, shows red borders and heading, an explanatory paragraph without commas, and a single “Ignore” button with a red frame and deep-blue text.
   * Clicking **Ignore** dismisses the popup until the user dips back below the threshold and exceeds it again.

5. **Single-Beam vs. Multibeam**

   * **Single-Beam (default)**: One bar moves downward at `strip_y_pos` pixels/frame; when it exits the bottom, it wraps around to the top.
   * **Multibeam (press M)**: Five bars, each offset by ⅕ of the cycle length (`(box_height + 10) / 5`), scroll together. Each bar’s on-screen position is `(strip_y_pos + i * spacing) % (box_height + 10)`.
   * Toggling back to single-beam preserves the bar’s position mod the original cycle so it does not “jump.”

6. **Help Overlay (press H)**

   * Freezes the underlying screen (copies it), dims it with a translucent black overlay, and draws a bordered help window up to 750×550 px (but constrained to the current window size).
   * Renders “Figure 19.1 – Drum Test Images at Different Shutter Speeds” (loads from disk if `figure_19_1.png/jpg/jpeg`, otherwise generates stripes algorithmically).
   * Below the figure, shows explanatory text about focal-plane shutter behavior from the Leica M3 Service Manual.
   * Fade-in/out animation for the help overlay’s alpha channel. Press **H** (or **Escape**) again to close.

7. **Dark/Light Mode (press T)**

   * **Dark Mode** (default): Black background, light-gray text, yellow titles, white bars.
   * **Light Mode**: White background, dark-gray text, deep-blue titles, dark-blue bars.
   * The status line “Mode: Dark” (or “Mode: Light”) updates live in the control panel.

8. **Window Resizing**

   * The application enforces a minimum width of 1200 px and minimum height of 800 px.
   * If the user attempts to shrink below those dimensions, the code clamps the size to 1200×800.
   * Otherwise, any enlarging/resizing dynamically recalculates the Shutter Test Area’s size and reflows text in the control panel so that no content ever overlaps or becomes clipped.

## How to Use

1. **Clone & Install**

   ```bash
   git clone https://github.com/yourusername/leica-pov-shutter-tester.git
   cd leica-pov-shutter-tester
   pip install pygame
   ```

   (Requires Python 3.6+ and Pygame.)

2. **Run the App**

   ```bash
   python main.py
   ```

   * On first launch, you’ll see an epilepsy warning. Check the box and wait 15 seconds before the **Continue** button lights up green. Click **Continue** to proceed.

3. **Main Screen Controls**

   * **Start/Stop**: Click the large button in the lower-left corner.
   * **Adjust Speed**:

     * Hold **UP** to increase by 1 px/frame; **Ctrl + UP** to increase by 5 each step.
     * Hold **DOWN** to decrease by 1 px/frame; **Ctrl + DOWN** to decrease by 5 each step.
   * **Toggle Multibeam**: Press **M** to switch between a single moving bar (Single-Beam) and five evenly spaced bars (Multibeam).
   * **Help Overlay**: Press **H** to open the help window showing “Figure 19.1” and explanatory text. Press **H** (or **Escape**) to close.
   * **Toggle Theme**: Press **T** to switch between Dark Mode and Light Mode.
   * **Quit**: Press **Escape** (from the main view) or click the window’s close button to exit.

4. **Speed Warning Logic**

   * The app reads your monitor’s refresh rate at startup and rounds to the nearest Hz (e.g., 74.96 Hz → 75 Hz).
   * In the control panel’s “Recommended Speeds” table, you’ll see “75 Hz → 75 px/frame” (for example).
   * If you set the scroll speed above that value, a semi-transparent popup warns you that the monitor can’t refresh lines fast enough, making the test invalid.
   * Click **Ignore** to dismiss. If you lower speed below “75 px/frame” and then exceed again later, the warning reappears.

5. **Viewing/Capturing**

   * Put your camera into a long-bulb exposure mode (e.g., 1 s or longer).
   * Point the camera at your computer monitor so the shutter test area fills the frame.
   * Start the animation at a known pixels/frame rate (e.g., 30 px/frame on a 60 Hz screen = 30 px/frame × 60 fps = 1800 px/sec).
   * The camera will capture diagonal bands in the resulting photograph. Compare those bands to Leica’s published examples (e.g., from the M3 service manual) to verify correct curtain tension and timing.

## Project Structure

```
leica-pov-shutter-tester/
├── main.py                 # Entry point, contains game loop and event handling
├── README.md               # This documentation
├── typeface.otf            # For interface
├── figure_19_1.png/jpg     # Leica diagram for the help overlay
├── build/                  # (Automatically created by PyInstaller)
│   └── main/               # Intermediate build files PyInstaller uses
│       └── build/
│       └── main/
│           ├── EXE-00.toc
│           ├── PKG-00.toc
│           ├── PYZ-00.pyz
│           ├── PYZ-00.toc
│           ├── Analysis-00.toc
│           ├── warn-main.txt
│           ├── xref-main.html
│           ├── base_library.zip
│           ├── localpycs/
│           │   ├── pyimod01_archive.pyc
│           │   ├── pyimod02_importers.pyc
│           │   ├── pyimod03_ctypes.pyc
│           │   ├── pyimod04_pywin32.pyc
│           │   └── struct.pyc
├── main.exe/               # Main executable for Windows x86
└── main.spec/              # The PyInstaller spec file (if you want to rebuild or tweak it)
```

* **`main.py`**:

  * Initializes Pygame, colors, fonts, and layout.
  * Manages global state variables: `strip_y_pos`, `speed`, `strip_active`, `multibeam_enabled`, etc.
  * Contains a `Renderer` class that draws every part of the UI (buttons, panels, shutter area, help overlay, warnings).
  * Contains a `GameLogic` class with helper methods for updating the strip animation, handling fade animations, and resizing.
  * The `while running:` loop handles keyboard/mouse events, continuous key-hold speed adjustments, mode toggles, and fade-in/fade-out logic for both the epilepsy warning and speed warning popups.

* **Key Methods in `Renderer`**

  1. **`draw_toggle_button()`**: Renders the single Start/Stop button in green or red.
  2. **`draw_instructions_and_table()`**: Renders controls, “About” text, current status lines, and the “Recommended Speeds” table.
  3. **`draw_shutter_test_area()`**: Outlines the left panel and calls either `draw_single_beam()` or `draw_multibeam()`, depending on mode.
  4. **`draw_single_beam()`**: Draws one horizontal bar moving at `strip_y_pos` and wraps.
  5. **`draw_multibeam()`**: Draws five evenly spaced bars that wrap continuously based on a cycle length.
  6. **`draw_help_overlay()`**: Renders a semi-opaque overlay plus a 750×550 (max) help window containing Figure 19.1 and explanatory text.
  7. **`draw_warning_screen()`**: Renders the epilepsy warning on first launch, including a 15 s countdown “Continue” button that remains disabled until the timer expires.
  8. **`draw_speed_warning_popup()`**: Renders a 550×300 px warning box when speed exceeds the monitor’s recommended px/frame. The box includes an English paragraph (no commas), and an “Ignore” button with a red frame and deep-blue text.

* **`GameLogic` Class**

  * `update_strip_animation()`: Increments `strip_y_pos` by `speed` px/frame. In single‐beam mode, wraps around when it leaves the bottom; in multibeam mode, wrapping is handled per‐bar in `draw_multibeam()`.
  * `update_help_animation()`: Manages fade-in/fade-out of the help overlay (alpha from 0 to 255).
  * `capture_background()`: Copies the current screen to freeze behind overlays.
  * `handle_resize()`: Enforces the 1200×800 minimum window, resizes Pygame and reflows layout.

## Installation & Dependencies

* **Python 3.6+**
* **Pygame**

  ```bash
  pip install pygame
  ```

(Optional: If you wish to bundle third-party fonts or images, place them under an `assets/` directory and update `ImageLoader.load_figure_image()` accordingly.)

## Usage

1. **Launch**

   ```bash
   python main.py
   ```

2. **Acknowledge Epilepsy Warning**

   * Check the box and wait 15 seconds.
   * Click **Continue** once enabled.

3. **Interact with Main Window**

   * **Start/Stop** by clicking the green/red button.
   * Hold **UP**/**DOWN** (±1 px/frame) or **Ctrl + UP**/**Ctrl + DOWN** (±5 px/frame) to change speed.
   * Press **M** to toggle Multibeam.
   * Press **T** to switch Dark/Light theme.
   * Press **H** for help overlay.
   * If you exceed the recommended px/frame (per your rounded refresh rate), a semi‐opaque “Speed Warning” popup appears. Click **Ignore** to dismiss. Lower speed below recommended to re-enable future warnings.

4. **Camera Setup**

   * Put your camera in bulb or a long continuous exposure mode (≥1 s).
   * Frame only the Shutter Test Area.
   * Start the animation at a known px/frame.
   * Review the captured image’s diagonal bands on film/sensor to verify shutter timing.

## Future Improvements

* **Web/Desktop Hybrid**

  * Deploy the same codebase via PyInstaller or as a web-based JavaScript/HTML5 Canvas version so that smartphones/tablets can run the test without Pygame.

* **Customizable Bar Height/Color**

  * Allow users to select bar thickness, color, or even pulse patterns to simulate different slit widths on screen.

* **Frame-Accurate Logging**

  * Add an option to log actual Pygame frame times (via `pygame.time.get_ticks()` or `Clock.get_time()`) and display jitter statistics, ensuring the application truly runs at 60 FPS or higher.

* **Offline/Printable Test Charts**

  * Generate PDF test charts that show the expected diagonal pattern at each shutter speed for cross-reference.

* **Localization**

  * Provide a built-in Vietnamese translation of all text, as well as English, Spanish, German, etc.

* **Integration with External Shutter Gauges**

  * Allow simultaneous use of a USB-connected photodiode sensor or Arduino interrupt to measure actual shutter timing, then overlay that data onto the digital bars for direct comparison.

## License

This project is released under the MIT License. Feel free to fork, modify, or incorporate it into your own workflow. Any contributions, bug fixes, or suggestions are greatly appreciated—please open a Pull Request or file an Issue on GitHub.

---

Thank you for trying out this Leica‐inspired persistence-of-vision shutter tester. Your feedback, bug reports, and suggestions for improvement are always welcome!
