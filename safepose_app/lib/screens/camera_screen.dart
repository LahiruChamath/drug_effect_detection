import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:camera/camera.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../theme/app_theme.dart';
import '../../utils/constants.dart';
import '../../widgets/pose_painter.dart';
import '../../services/pose_service.dart';
import '../../services/pose_interface.dart';
import 'analyzing_screen.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  // Camera
  CameraController? _cameraController;
  List<CameraDescription>? _cameras;
  CameraDescription? _currentCamera;
  bool _isCameraInitialized = false;

  // Pose Detection
  List<BasePose> _currentPoses = [];
  bool _showSkeleton = true;

  // Recording State
  bool _isRecording = false;
  bool _isCountingDown = false;
  int _countdown = 3;
  int _recordingSeconds = 0;
  Timer? _countdownTimer;
  Timer? _recordingTimer;

  // Detection
  bool _bodyDetected = false;
  String _guidanceText = 'Position your full body in frame';
  int _lostFramesCount = 0;

  @override
  void initState() {
    super.initState();
    poseService.initialize();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras == null || _cameras!.isEmpty) return;

      // Load preference
      final prefs = await SharedPreferences.getInstance();
      final prefString = prefs.getString('camera_preference') ?? 'back';
      final preferredDirection = prefString == 'front'
          ? CameraLensDirection.front
          : CameraLensDirection.back;

      // On web, try to find a camera that isn't an "iPhone" (Continuity Camera) if possible
      if (kIsWeb) {
        _currentCamera = _cameras!.firstWhere(
          (c) => !c.name.contains('iPhone') && !c.name.contains('Continuity'),
          orElse: () => _cameras!.first,
        );
      } else {
        _currentCamera = _cameras!.firstWhere(
          (c) => c.lensDirection == preferredDirection,
          orElse: () => _cameras!.first,
        );
      }

      await _setupCamera(_currentCamera!);
    } catch (e) {
      debugPrint('Camera init error: $e');
    }
  }

  Future<void> _setupCamera(CameraDescription camera) async {
    // Dispose old controller
    if (_cameraController != null) {
      await _cameraController!.dispose();
    }

    _cameraController = CameraController(
      camera,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    await _cameraController!.initialize();

    await _cameraController!.initialize();

    // Start image stream for pose detection ONLY on mobile
    if (!kIsWeb) {
      await _cameraController!.startImageStream(_processCameraFrame);
    } else {
      // On web, we skip ML Kit overlay and just allow recording immediately
      if (mounted) {
        setState(() {
          _bodyDetected = true;
          _showSkeleton = false;
          _guidanceText = 'Ready to record';
        });
      }
    }

    if (mounted) {
      setState(() {
        _currentCamera = camera;
        _isCameraInitialized = true;
      });
    }
  }

  void _processCameraFrame(CameraImage image) async {
    if (_currentCamera == null || kIsWeb) return;

    final poses = await poseService.processFrame(image, _currentCamera!);
    if (poses == null) return; // Frame skipped, don't change state

    if (mounted) {
      setState(() {
        if (poses.isNotEmpty) {
          _currentPoses = poses;
          _bodyDetected = true;
          _lostFramesCount = 0;
        } else {
          _lostFramesCount++;
          // Give a short grace period before losing the target completely
          if (_lostFramesCount > 5) {
            _currentPoses = [];
            _bodyDetected = false;
          }
        }
        
        _guidanceText = _bodyDetected
            ? 'Body detected! Ready to scan'
            : 'Position your full body in frame';
      });
    }
  }

  Future<void> _switchCamera() async {
    if (_cameras == null || _cameras!.length < 2) return;
    if (_isRecording || _isCountingDown) return;

    setState(() => _isCameraInitialized = false);

    final currentLens = _currentCamera!.lensDirection;
    final otherCameras = _cameras!.where((c) => c.lensDirection != currentLens).toList();
    
    final newCamera = otherCameras.isNotEmpty 
        ? otherCameras.first 
        : _cameras!.firstWhere((c) => c != _currentCamera, orElse: () => _cameras!.first);

    await _setupCamera(newCamera);
  }

  void _startCountdown() {
    if (!_bodyDetected) return;

    setState(() {
      _isCountingDown = true;
      _countdown = 3;
    });

    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown > 1) {
        setState(() => _countdown--);
      } else {
        timer.cancel();
        setState(() => _isCountingDown = false);
        _startRecording();
      }
    });
  }

  Future<void> _startRecording() async {
    if (_cameraController == null) return;

    try {
      // On Android, starting video recording kills the image stream.
      // The skeleton will show the last detected pose during recording,
      // which is expected behavior — the video itself captures the motion
      // data that the API needs for analysis.
      await _cameraController!.startVideoRecording();

      poseService.resetStats();

      setState(() {
        _isRecording = true;
        _recordingSeconds = Constants.recordingDuration;
      });

      _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        if (_recordingSeconds > 1) {
          setState(() => _recordingSeconds--);
        } else {
          timer.cancel();
          _stopRecording();
        }
      });
    } catch (e) {
      debugPrint('Recording start error: $e');
    }
  }

  Future<void> _stopRecording() async {
    if (_cameraController == null || !_cameraController!.value.isRecordingVideo) {
      return;
    }

    try {
      final videoFile = await _cameraController!.stopVideoRecording();
      final videoPath = videoFile.path;

      setState(() => _isRecording = false);

      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => AnalyzingScreen(videoPath: videoPath),
          ),
        );
      }
    } catch (e) {
      debugPrint('Recording stop error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save video recording.')),
        );
      }
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _recordingTimer?.cancel();
    _cameraController?.dispose();
    poseService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ── Camera Preview + Pose Overlay ──
          if (_isCameraInitialized && _cameraController != null)
            _buildCameraWithPose()
          else
            const Center(
              child: CircularProgressIndicator(color: AppTheme.primaryColor),
            ),

          // ── Top Bar ──
          _buildTopBar(),

          // ── Body Detection Indicator ──
          if (!_isRecording && !_isCountingDown) _buildDetectionIndicator(),

          // ── Countdown Overlay ──
          if (_isCountingDown) _buildCountdownOverlay(),

          // ── Recording Overlay ──
          if (_isRecording) _buildRecordingOverlay(),

          // ── Bottom Controls ──
          _buildBottomControls(),
        ],
      ),
    );
  }

  Widget _buildCameraWithPose() {
    final size = MediaQuery.of(context).size;
    
    // Web usually has more varying aspect ratios, so we use a safer scaling
    double scale;
    if (kIsWeb) {
      // On web, we often just want to fit the camera preview without excessive scaling
      // This avoids the "super zoom" on wide macbook cameras
      scale = 1.0; 
    } else {
      scale = size.aspectRatio * _cameraController!.value.aspectRatio;
      if (scale < 1) scale = 1 / scale;
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        // We know Stack fits expand, so constraints are the screen size
        final screenWidth = constraints.maxWidth;
        final screenHeight = constraints.maxHeight;
        
        // When we do Transform.scale, the actual rendered size expands beyond the bounds
        final renderedWidth = screenWidth * scale;
        final renderedHeight = screenHeight * scale;

        return Stack(
          fit: StackFit.expand,
          children: [
            // Camera Preview
            Transform.scale(
              scale: scale,
              child: Center(
                child: Stack(
                  children: [
                    // Camera Preview constraints itself using aspect ratio
                    CameraPreview(_cameraController!),
                    
                    // Pose Skeleton Overlay fills the exact preview bounds
                    if (_showSkeleton && _currentPoses.isNotEmpty && _currentCamera != null)
                      Positioned.fill(
                        child: CustomPaint(
                          painter: PosePainter(
                            poses: _currentPoses,
                            // Pass the portrait orientation size (swapped)
                            imageSize: Size(
                              _cameraController!.value.previewSize!.height,
                              _cameraController!.value.previewSize!.width,
                            ),
                            rotation: _currentCamera!.sensorOrientation,
                            cameraDirection: _currentCamera!.lensDirection,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildTopBar() {
    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildCircleButton(
                icon: Icons.close,
                onTap: () => Navigator.pop(context),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.black38,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  'SafePose Scanner',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Row(
                children: [
                  _buildCircleButton(
                    icon: _showSkeleton ? Icons.visibility : Icons.visibility_off,
                    onTap: () => setState(() => _showSkeleton = !_showSkeleton),
                  ),
                  const SizedBox(width: 8),
                  _buildCircleButton(
                    icon: Icons.flip_camera_ios,
                    onTap: _switchCamera,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCircleButton({required IconData icon, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40,
        height: 40,
        decoration: const BoxDecoration(
          color: Colors.black38,
          shape: BoxShape.circle,
        ),
        child: Icon(icon, color: Colors.white, size: 22),
      ),
    );
  }

  Widget _buildDetectionIndicator() {
    return Positioned(
      top: 100,
      left: 0,
      right: 0,
      child: Center(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          decoration: BoxDecoration(
            color: _bodyDetected
                ? AppTheme.successColor.withOpacity(0.9)
                : Colors.black54,
            borderRadius: BorderRadius.circular(30),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _bodyDetected ? Icons.check_circle : Icons.person_search,
                color: Colors.white,
                size: 18,
              ),
              const SizedBox(width: 8),
              Text(
                _guidanceText,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCountdownOverlay() {
    return Container(
      color: Colors.black38,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Get Ready!',
              style: TextStyle(
                color: Colors.white.withOpacity(0.8),
                fontSize: 20,
              ),
            ),
            const SizedBox(height: 20),
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: Colors.black54,
                shape: BoxShape.circle,
                border: Border.all(color: AppTheme.primaryColor, width: 4),
              ),
              child: Center(
                child: Text(
                  '$_countdown',
                  style: const TextStyle(
                    fontSize: 60,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecordingOverlay() {
    final progress = (Constants.recordingDuration - _recordingSeconds) / Constants.recordingDuration;

    return Positioned(
      bottom: 150,
      left: 0,
      right: 0,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.red.withOpacity(0.9),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'REC  $_recordingSeconds s',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: LinearProgressIndicator(
                value: progress,
                backgroundColor: Colors.white24,
                valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryColor),
                minHeight: 6,
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Keep still • Stay in frame',
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomControls() {
    return Positioned(
      bottom: 0,
      left: 0,
      right: 0,
      child: SafeArea(
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 30),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Skeleton toggle info
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _showSkeleton ? Icons.visibility : Icons.visibility_off,
                    color: Colors.white54,
                    size: 24,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _showSkeleton ? 'Skeleton ON' : 'Skeleton OFF',
                    style: const TextStyle(color: Colors.white54, fontSize: 10),
                  ),
                ],
              ),

              // Record Button
              if (!_isRecording && !_isCountingDown)
                GestureDetector(
                  onTap: _bodyDetected ? _startCountdown : null,
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: _bodyDetected ? Colors.white : Colors.white30,
                        width: 4,
                      ),
                    ),
                    child: Center(
                      child: Container(
                        width: 60,
                        height: 60,
                        decoration: BoxDecoration(
                          color: _bodyDetected ? Colors.red : Colors.red.withOpacity(0.3),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                  ),
                )
              else
                const SizedBox(width: 80),

              // Detection rate
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _bodyDetected ? Icons.person : Icons.person_off,
                    color: _bodyDetected ? AppTheme.primaryColor : Colors.white54,
                    size: 24,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _bodyDetected ? 'Detected' : 'Not Found',
                    style: TextStyle(
                      color: _bodyDetected ? AppTheme.primaryColor : Colors.white54,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
