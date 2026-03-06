import 'dart:async';
// ignore: avoid_web_libraries_in_flutter
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:web/web.dart' as web;
import 'dart:js_interop';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import 'analyzing_screen.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  bool _isRecording = false;
  int _countdown = 3;
  int _recordingSeconds = 0;
  Timer? _countdownTimer;
  Timer? _recordingTimer;
  bool _showCountdown = false;
  bool _cameraReady = false;
  bool _cameraError = false;
  final String _viewId = 'webcam-${DateTime.now().millisecondsSinceEpoch}';
  web.MediaStream? _stream;

  @override
  void initState() {
    super.initState();
    if (kIsWeb) {
      _initWebCamera();
    }
  }

  Future<void> _initWebCamera() async {
    try {
      // Create mirrored <video> element
      final video = web.HTMLVideoElement()
        ..autoplay = true
        ..muted = true
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.objectFit = 'cover'
        ..style.transform = 'scaleX(-1)';

      // Register platform view
      ui_web.platformViewRegistry.registerViewFactory(
        _viewId,
        (int id) => video,
      );

      // Request camera access
      final constraints = web.MediaStreamConstraints(video: true.toJS);
      final stream = await web.window.navigator.mediaDevices
          .getUserMedia(constraints)
          .toDart;

      _stream = stream;
      video.srcObject = stream;

      if (mounted) {
        setState(() {
          _cameraReady = true;
          _cameraError = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _cameraError = true;
          _cameraReady = false;
        });
      }
    }
  }

  void _stopStream() {
    if (_stream != null) {
      final tracks = _stream!.getVideoTracks().toDart;
      for (final t in tracks) {
        t.stop();
      }
      _stream = null;
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _recordingTimer?.cancel();
    if (kIsWeb) _stopStream();
    super.dispose();
  }

  void _startCountdown() {
    setState(() {
      _showCountdown = true;
      _countdown = 3;
    });
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown > 1) {
        setState(() => _countdown--);
      } else {
        timer.cancel();
        _startRecording();
      }
    });
  }

  void _startRecording() {
    setState(() {
      _showCountdown = false;
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
  }

  void _stopRecording() {
    setState(() => _isRecording = false);
    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => const AnalyzingScreen(
            videoPath: 'web_recording',
            poseFrames: null,
          ),
        ),
      );
    }
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
        title: const Text('Camera',
            style: TextStyle(color: Colors.white)),
      ),
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ── Camera Feed ─────────────────────────────────────────
          if (kIsWeb && _cameraReady)
            HtmlElementView(viewType: _viewId)
          else if (kIsWeb && _cameraError)
            _buildErrorPlaceholder()
          else
            _buildLoadingPlaceholder(),

          // ── Overlays ─────────────────────────────────────────────
          SafeArea(
            child: Column(
              children: [
                const Spacer(),

                if (_showCountdown) _buildCountdownBadge(),
                if (_isRecording) _buildRecordingIndicator(),

                const Spacer(),

                if (_isRecording) _buildProgressBar(),

                const SizedBox(height: 20),

                _buildInstructionPill(),

                const SizedBox(height: 30),

                if (!_isRecording && !_showCountdown) _buildRecordButton(),

                const SizedBox(height: 40),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingPlaceholder() => Container(
        color: Colors.grey.shade900,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(color: AppTheme.primaryColor),
              const SizedBox(height: 16),
              Text(
                kIsWeb ? 'Starting camera...' : 'Camera Preview',
                style: const TextStyle(color: Colors.white70, fontSize: 16),
              ),
            ],
          ),
        ),
      );

  Widget _buildErrorPlaceholder() => Container(
        color: Colors.grey.shade900,
        child: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.no_photography, size: 80, color: Colors.white54),
              SizedBox(height: 16),
              Text('Camera access denied',
                  style: TextStyle(color: Colors.white70, fontSize: 18)),
              SizedBox(height: 8),
              Text(
                'Allow camera permission in your browser\nand reload the page.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white38, fontSize: 13),
              ),
            ],
          ),
        ),
      );

  Widget _buildCountdownBadge() => Container(
        width: 120,
        height: 120,
        decoration: const BoxDecoration(
            color: Colors.black54, shape: BoxShape.circle),
        child: Center(
          child: Text('$_countdown',
              style: const TextStyle(
                  fontSize: 60,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryColor)),
        ),
      );

  Widget _buildRecordingIndicator() => Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                  width: 12,
                  height: 12,
                  decoration: const BoxDecoration(
                      color: Colors.red, shape: BoxShape.circle)),
              const SizedBox(width: 8),
              const Text('RECORDING',
                  style: TextStyle(
                      color: Colors.red,
                      fontWeight: FontWeight.bold,
                      fontSize: 16)),
            ],
          ),
          const SizedBox(height: 20),
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: Colors.black54,
              shape: BoxShape.circle,
              border: Border.all(color: AppTheme.primaryColor, width: 4),
            ),
            child: Center(
              child: Text('$_recordingSeconds',
                  style: const TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.bold,
                      color: Colors.white)),
            ),
          ),
          const SizedBox(height: 8),
          const Text('seconds remaining',
              style: TextStyle(color: Colors.white70)),
        ],
      );

  Widget _buildProgressBar() => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: LinearProgressIndicator(
            value: (Constants.recordingDuration - _recordingSeconds) /
                Constants.recordingDuration,
            backgroundColor: Colors.white24,
            valueColor:
                const AlwaysStoppedAnimation<Color>(AppTheme.primaryColor),
            minHeight: 8,
          ),
        ),
      );

  Widget _buildInstructionPill() => Container(
        padding:
            const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
            color: Colors.black54,
            borderRadius: BorderRadius.circular(30)),
        child: Text(
          _isRecording
              ? 'Keep still • Stay in frame'
              : _cameraError
                  ? 'Camera unavailable — tap to proceed anyway'
                  : 'Press button to start recording',
          style: const TextStyle(color: Colors.white),
          textAlign: TextAlign.center,
        ),
      );

  Widget _buildRecordButton() => GestureDetector(
        onTap: _startCountdown,
        child: Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 4)),
          child: Center(
            child: Container(
              width: 60,
              height: 60,
              decoration: const BoxDecoration(
                  color: Colors.red, shape: BoxShape.circle),
            ),
          ),
        ),
      );
}
