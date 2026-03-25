import 'package:flutter/material.dart';
import 'package:camera/camera.dart';

class UniversalCameraView extends StatefulWidget {
  final Widget Function(BuildContext) loadingBuilder;
  final Widget Function(BuildContext, String) errorBuilder;
  final VoidCallback onReady;

  const UniversalCameraView({
    super.key,
    required this.loadingBuilder,
    required this.errorBuilder,
    required this.onReady,
  });

  @override
  State<UniversalCameraView> createState() => _UniversalCameraViewState();
}

class _UniversalCameraViewState extends State<UniversalCameraView> {
  CameraController? _controller;
  bool _cameraError = false;
  String _errorMessage = '';

  @override
  void initState() {
    super.initState();
    _initMobileCamera();
  }

  Future<void> _initMobileCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw Exception('No cameras found');
      }
      
      // Try to find the front camera
      CameraDescription? selectedCamera;
      for (final camera in cameras) {
        if (camera.lensDirection == CameraLensDirection.front) {
          selectedCamera = camera;
          break;
        }
      }
      // Fallback to the first available camera
      selectedCamera ??= cameras.first;

      _controller = CameraController(
        selectedCamera,
        ResolutionPreset.high,
        enableAudio: false,
      );

      await _controller!.initialize();

      if (mounted) {
        setState(() {});
        widget.onReady();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _cameraError = true;
          _errorMessage = e.toString();
        });
      }
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_cameraError) {
      return widget.errorBuilder(context, _errorMessage);
    }
    if (_controller == null || !_controller!.value.isInitialized) {
      return widget.loadingBuilder(context);
    }
    final size = MediaQuery.of(context).size;
    var scale = size.aspectRatio * _controller!.value.aspectRatio;

    if (scale < 1) scale = 1 / scale;

    return Transform.scale(
      scale: scale,
      child: Center(
        child: CameraPreview(_controller!),
      ),
    );
  }
}
