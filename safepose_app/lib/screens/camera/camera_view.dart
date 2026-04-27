export 'camera_view_stub.dart'
    if (dart.library.html) 'camera_view_web.dart'
    if (dart.library.io) 'camera_view_mobile.dart';
