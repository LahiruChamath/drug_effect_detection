import 'package:camera/camera.dart';
import 'pose_interface.dart';

class PoseDetectionServiceImpl implements PoseDetectionService {
  @override
  void initialize() {}

  @override
  Future<List<BasePose>?> processFrame(CameraImage image, CameraDescription camera) async {
    return null;
  }

  @override
  void resetStats() {}

  @override
  Future<void> dispose() async {}

  @override
  int get totalFrames => 0;
  @override
  int get detectedFrames => 0;
  @override
  double get detectionRate => 0.0;
}
