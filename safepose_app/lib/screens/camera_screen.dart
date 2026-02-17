import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import 'analyzing_screen.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;
  List<CameraDescription>? _cameras;
  bool _isInitialized = false;
  bool _isRecording = false;
  int _countdown = 3;
  int _recordingSeconds = 0;
  Timer? _countdownTimer;
  Timer? _recordingTimer;
  String? _videoPath;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      
      if (_cameras != null && _cameras!.isNotEmpty) {
        // Use front camera if available
        final frontCamera = _cameras!.firstWhere(
          (camera) => camera.lensDirection == CameraLensDirection.front,
          orElse: () => _cameras!.first,
        );

        _controller = CameraController(
          frontCamera,
          ResolutionPreset.medium,
          enableAudio: false,
        );

        await _controller!.initialize();
        
        if (mounted) {
          setState(() => _isInitialized = true);
        }
      }
    } catch (e) {
      debugPrint('Error initializing camera: $e');
    }
  }

  void _startCountdown() {
    setState(() => _countdown = 3);
    
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown > 1) {
        setState(() => _countdown--);
      } else {
        timer.cancel();
        _startRecording();
      }
    });
  }

  Future<void> _startRecording() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    try {
      // Get temp directory
      final directory = await getTemporaryDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      _videoPath = '${directory.path}/safepose_$timestamp.mp4';

      await _controller!.startVideoRecording();
      
      setState(() {
        _isRecording = true;
        _recordingSeconds = Constants.recordingDuration;
      });

      // Recording countdown
      _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        if (_recordingSeconds > 1) {
          setState(() => _recordingSeconds--);
        } else {
          timer.cancel();
          _stopRecording();
        }
      });
    } catch (e) {
      debugPrint('Error starting recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    if (_controller == null || !_controller!.value.isRecordingVideo) return;

    try {
      final videoFile = await _controller!.stopVideoRecording();
      _videoPath = videoFile.path;

      setState(() => _isRecording = false);

      // Navigate to analyzing screen
      if (mounted && _videoPath != null) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => AnalyzingScreen(videoPath: _videoPath!),
          ),
        );
      }
    } catch (e) {
      debugPrint('Error stopping recording: $e');
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _recordingTimer?.cancel();
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Camera Preview
          if (_isInitialized && _controller != null)
            CameraPreview(_controller!)
          else
            const Center(
              child: CircularProgressIndicator(
                color: AppTheme.primaryColor,
              ),
            ),

          // Overlay
          SafeArea(
            child: Column(
              children: [
                const Spacer(),
                
                // Countdown or Recording indicator
                if (_countdown > 0 && !_isRecording && _countdownTimer != null)
                  Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      shape: BoxShape.circle,
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

                if (_isRecording)
                  Column(
                    children: [
                      // Recording indicator
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 12,
                            height: 12,
                            decoration: const BoxDecoration(
                              color: Colors.red,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'RECORDING',
                            style: TextStyle(
                              color: Colors.red,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20),
                      
                      // Countdown circle
                      Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                          color: Colors.black54,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: AppTheme.primaryColor,
                            width: 4,
                          ),
                        ),
                        child: Center(
                          child: Text(
                            '$_recordingSeconds',
                            style: const TextStyle(
                              fontSize: 40,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'seconds remaining',
                        style: TextStyle(color: Colors.white70),
                      ),
                    ],
                  ),

                const Spacer(),

                // Progress bar
                if (_isRecording)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 40),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: LinearProgressIndicator(
                        value: (Constants.recordingDuration - _recordingSeconds) / 
                               Constants.recordingDuration,
                        backgroundColor: Colors.white24,
                        valueColor: const AlwaysStoppedAnimation<Color>(
                          AppTheme.primaryColor,
                        ),
                        minHeight: 8,
                      ),
                    ),
                  ),

                const SizedBox(height: 20),

                // Instructions
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: Text(
                    _isRecording
                        ? 'Keep still • Stay in frame'
                        : 'Press button to start recording',
                    style: const TextStyle(color: Colors.white),
                  ),
                ),

                const SizedBox(height: 30),

                // Record Button
                if (!_isRecording && _countdownTimer == null)
                  GestureDetector(
                    onTap: _isInitialized ? _startCountdown : null,
                    child: Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 4),
                      ),
                      child: Center(
                        child: Container(
                          width: 60,
                          height: 60,
                          decoration: const BoxDecoration(
                            color: Colors.red,
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                    ),
                  ),

                const SizedBox(height: 40),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
