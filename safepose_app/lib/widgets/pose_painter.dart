import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../services/pose_interface.dart';

class PosePainter extends CustomPainter {
  final List<BasePose> poses;
  final Size imageSize;
  final int rotation; // Raw sensor orientation (e.g. 90, 270)
  final CameraLensDirection cameraDirection;

  PosePainter({
    required this.poses,
    required this.imageSize,
    required this.rotation,
    required this.cameraDirection,
  });

  static const List<List<PoseLandmarkType>> _connections = [
    // Face
    [PoseLandmarkType.leftEar, PoseLandmarkType.leftEye],
    [PoseLandmarkType.rightEar, PoseLandmarkType.rightEye],
    [PoseLandmarkType.leftEye, PoseLandmarkType.nose],
    [PoseLandmarkType.rightEye, PoseLandmarkType.nose],
    // Upper body
    [PoseLandmarkType.leftShoulder, PoseLandmarkType.rightShoulder],
    [PoseLandmarkType.leftShoulder, PoseLandmarkType.leftElbow],
    [PoseLandmarkType.leftElbow, PoseLandmarkType.leftWrist],
    [PoseLandmarkType.rightShoulder, PoseLandmarkType.rightElbow],
    [PoseLandmarkType.rightElbow, PoseLandmarkType.rightWrist],
    // Torso
    [PoseLandmarkType.leftShoulder, PoseLandmarkType.leftHip],
    [PoseLandmarkType.rightShoulder, PoseLandmarkType.rightHip],
    [PoseLandmarkType.leftHip, PoseLandmarkType.rightHip],
    // Lower body
    [PoseLandmarkType.leftHip, PoseLandmarkType.leftKnee],
    [PoseLandmarkType.leftKnee, PoseLandmarkType.leftAnkle],
    [PoseLandmarkType.rightHip, PoseLandmarkType.rightKnee],
    [PoseLandmarkType.rightKnee, PoseLandmarkType.rightAnkle],
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final activeSize = size;

    final linePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..color = const Color(0xFF00C896);

    final jointPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = const Color(0xFF00C896);

    final jointOutlinePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0
      ..color = Colors.white;

    final keyJointPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = Colors.white;

    for (final pose in poses) {
      // Draw connections
      for (final connection in _connections) {
        final start = pose.landmarks[connection[0]];
        final end = pose.landmarks[connection[1]];
        if (start != null && end != null) {
          if (start.likelihood > 0.5 && end.likelihood > 0.5) {
            canvas.drawLine(
              _transformPoint(Offset(start.x, start.y), activeSize),
              _transformPoint(Offset(end.x, end.y), activeSize),
              linePaint,
            );
          }
        }
      }

      // Draw joint dots
      for (final landmark in pose.landmarks.values) {
        if (landmark.likelihood > 0.5) {
          final point = _transformPoint(
            Offset(landmark.x, landmark.y),
            activeSize,
          );
          final isKey = _isKeyJoint(landmark.type);
          final radius = isKey ? 8.0 : 5.0;
          canvas.drawCircle(point, radius + 2, jointOutlinePaint);
          canvas.drawCircle(point, radius, isKey ? keyJointPaint : jointPaint);
        }
      }
    }
  }

  bool _isKeyJoint(PoseLandmarkType type) {
    return [
      PoseLandmarkType.nose,
      PoseLandmarkType.leftShoulder, PoseLandmarkType.rightShoulder,
      PoseLandmarkType.leftElbow, PoseLandmarkType.rightElbow,
      PoseLandmarkType.leftWrist, PoseLandmarkType.rightWrist,
      PoseLandmarkType.leftHip, PoseLandmarkType.rightHip,
      PoseLandmarkType.leftKnee, PoseLandmarkType.rightKnee,
      PoseLandmarkType.leftAnkle, PoseLandmarkType.rightAnkle,
    ].contains(type);
  }

  Offset _transformPoint(Offset point, Size canvasSize) {
    double x = point.dx;
    double y = point.dy;

    // ML Kit returns coordinates in the original (non-mirrored) camera frame.
    // On iOS, CameraPreview already displays the front camera as a mirror,
    // so we do NOT flip x here — the raw coordinates already match the
    // mirrored preview.

    // Scale exactly to the UI preview box
    final scaleX = canvasSize.width / imageSize.width;
    final scaleY = canvasSize.height / imageSize.height;

    return Offset(x * scaleX, y * scaleY);
  }

  @override
  bool shouldRepaint(PosePainter oldDelegate) => oldDelegate.poses != poses;
}
