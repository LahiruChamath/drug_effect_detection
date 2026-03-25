import 'package:flutter/material.dart';
import 'package:camera/camera.dart';

class UniversalCameraView extends StatefulWidget {
  final Widget Function(BuildContext) loadingBuilder;
  final Widget Function(BuildContext, String) errorBuilder;
  final VoidCallback onReady;
  final CameraLensDirection initialDirection;

  const UniversalCameraView({
    super.key,
    required this.loadingBuilder,
    required this.errorBuilder,
    required this.onReady,
    this.initialDirection = CameraLensDirection.back,
  });

  @override
  State<UniversalCameraView> createState() => UniversalCameraViewState();
}

class UniversalCameraViewState extends State<UniversalCameraView> {
  @override
  Widget build(BuildContext context) {
    return widget.errorBuilder(context, 'Platform not supported');
  }

  Future<void> startRecording() async {}
  
  Future<XFile?> stopRecording() async {
    return null;
  }
}

