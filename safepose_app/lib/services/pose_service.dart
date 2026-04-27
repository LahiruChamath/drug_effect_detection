import 'package:flutter/foundation.dart' show kIsWeb;
import 'pose_interface.dart';
import 'pose_service_mobile.dart' if (dart.library.js) 'pose_service_web.dart' if (dart.library.html) 'pose_service_web.dart';

// Unified global service
final PoseDetectionService poseService = PoseDetectionServiceImpl();

