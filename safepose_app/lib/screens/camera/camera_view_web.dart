// ignore: avoid_web_libraries_in_flutter
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:web/web.dart' as web;
import 'dart:js_interop';

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
  bool _cameraReady = false;
  bool _cameraError = false;
  late String _viewId;
  web.MediaStream? _stream;

  @override
  void initState() {
    super.initState();
    _viewId = 'webcam-${DateTime.now().millisecondsSinceEpoch}';
    _initWebCamera();
  }

  Future<void> _initWebCamera() async {
    try {
      final video = web.HTMLVideoElement()
        ..autoplay = true
        ..muted = true
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.objectFit = 'cover'
        ..style.transform = 'scaleX(-1)';

      ui_web.platformViewRegistry.registerViewFactory(
        _viewId,
        (int id) => video,
      );

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
        widget.onReady();
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

  @override
  void dispose() {
    if (_stream != null) {
      final tracks = _stream!.getVideoTracks().toDart;
      for (final t in tracks) {
        t.stop();
      }
      _stream = null;
    }
    super.dispose();
  }

  Future<void> startRecording() async {
    // Web stub: not implemented here
  }

  Future<XFile?> stopRecording() async {
    // Web stub: not implemented here
    return null;
  }

  @override
  Widget build(BuildContext context) {
    if (_cameraError) {
      return widget.errorBuilder(context, 'Camera access denied');
    }
    if (!_cameraReady) {
      return widget.loadingBuilder(context);
    }
    return HtmlElementView(viewType: _viewId);
  }
}
