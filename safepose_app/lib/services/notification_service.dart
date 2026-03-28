import 'api_service.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final ApiService _apiService = ApiService();

  Future<void> initialize() async {
    print('ℹ️ NotificationService: Firebase plugins removed due to iOS dependency conflicts.');
    print('ℹ️ Push notifications are handled server-side only for now.');
  }

  Future<void> syncToken() async {
    // Stub: No longer fetching FCM token client-side
    // Future implementation could use APNs directly or alternative push service
  }
}

