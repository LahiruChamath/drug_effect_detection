import 'package:camera/camera.dart';

// Shared types that don't depend on ML Kit
abstract class BasePose {
  Map<dynamic, BaseLandmark> get landmarks;
}

abstract class BaseLandmark {
  double get x;
  double get y;
  double get likelihood;
  PoseLandmarkType get type;
}

enum PoseLandmarkType {
  leftEar, rightEar, leftEye, rightEye, nose,
  leftShoulder, rightShoulder, leftElbow, rightElbow, leftWrist, rightWrist,
  leftHip, rightHip, leftKnee, rightKnee, leftAnkle, rightAnkle
}

abstract class PoseDetectionService {
  void initialize();
  Future<List<BasePose>?> processFrame(CameraImage image, CameraDescription camera);
  void resetStats();
  Future<void> dispose();
  
  int get totalFrames;
  int get detectedFrames;
  double get detectionRate;
}
