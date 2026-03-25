import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart' as ml;
import 'package:google_mlkit_commons/google_mlkit_commons.dart' as ml;
import 'package:flutter/foundation.dart';
import 'dart:ui';
import 'pose_interface.dart';

class PoseDetectionServiceImpl implements PoseDetectionService {
  ml.PoseDetector? _poseDetector;
  bool _isProcessing = false;
  bool _isInitialized = false;

  int _totalFrames = 0;
  int _detectedFrames = 0;

  @override
  int get totalFrames => _totalFrames;
  @override
  int get detectedFrames => _detectedFrames;
  @override
  double get detectionRate => _totalFrames == 0 ? 0 : _detectedFrames / _totalFrames;

  @override
  void initialize() {
    final options = ml.PoseDetectorOptions(
      mode: ml.PoseDetectionMode.stream,
      model: ml.PoseDetectionModel.accurate,
    );
    _poseDetector = ml.PoseDetector(options: options);
    _isInitialized = true;
    _totalFrames = 0;
    _detectedFrames = 0;
  }

  @override
  Future<List<BasePose>?> processFrame(CameraImage image, CameraDescription camera) async {
    if (!_isInitialized || _poseDetector == null) return null;
    if (_isProcessing) return null; // Skipped frame

    _isProcessing = true;
    _totalFrames++;

    try {
      final inputImage = _convertCameraImage(image, camera);
      if (inputImage == null) {
        _isProcessing = false;
        return null;
      }

      final poses = await _poseDetector!.processImage(inputImage);
      if (poses.isNotEmpty) {
        _detectedFrames++;
      }

      _isProcessing = false;
      return poses.map((p) => MobilePose(p)).toList();
    } catch (e) {
      debugPrint('Pose detection error: $e');
      _isProcessing = false;
      return null;
    }
  }

  ml.InputImage? _convertCameraImage(CameraImage image, CameraDescription camera) {
    try {
      final rotation = ml.InputImageRotationValue.fromRawValue(camera.sensorOrientation);
      if (rotation == null) return null;

      final format = ml.InputImageFormatValue.fromRawValue(image.format.raw);
      if (format == null) return null;

      final bytes = Uint8List.fromList(
        image.planes.fold<List<int>>(
          [],
          (List<int> previousValue, element) => previousValue..addAll(element.bytes),
        ),
      );

      final inputImageData = ml.InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: image.planes.first.bytesPerRow,
      );

      return ml.InputImage.fromBytes(
        bytes: bytes,
        metadata: inputImageData,
      );
    } catch (e) {
      debugPrint('Image conversion error: $e');
      return null;
    }
  }

  @override
  void resetStats() {
    _totalFrames = 0;
    _detectedFrames = 0;
  }

  @override
  Future<void> dispose() async {
    await _poseDetector?.close();
    _isInitialized = false;
  }
}

class MobilePose implements BasePose {
  final ml.Pose _pose;
  MobilePose(this._pose);

  @override
  Map<dynamic, BaseLandmark> get landmarks {
    final Map<PoseLandmarkType, BaseLandmark> mapped = {};
    
    // Explicitly map ML Kit Landmark Types to our Interface Types
    _pose.landmarks.forEach((key, value) {
      // Use name-based matching to cross between package enums and our enum
      for (var type in PoseLandmarkType.values) {
        if (type.name == key.name) {
          mapped[type] = MobileLandmark(value, type);
          break;
        }
      }
    });
    
    return mapped;
  }
}

class MobileLandmark implements BaseLandmark {
  final ml.PoseLandmark _landmark;
  @override
  final PoseLandmarkType type;
  
  MobileLandmark(this._landmark, this.type);

  @override
  double get x => _landmark.x;
  @override
  double get y => _landmark.y;
  @override
  double get likelihood => _landmark.likelihood;
}
