class ScanResult {
  final String scanId;
  final String prediction;
  final double confidence;
  final Map<String, double> probabilities;
  final List<String> indicators;
  final double detectionRate;
  final int framesAnalyzed;
  final double duration;
  final DateTime? timestamp;

  ScanResult({
    required this.scanId,
    required this.prediction,
    required this.confidence,
    required this.probabilities,
    this.indicators = const [],
    this.detectionRate = 1.0,
    required this.framesAnalyzed,
    this.duration = 0.0,
    this.timestamp,
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    // Generate indicators based on prediction
    List<String> generateIndicators(String prediction, double confidence) {
      switch (prediction.toLowerCase()) {
        case 'none':
          return [
            'Normal movement patterns',
            'Stable posture detected',
            'Consistent timing observed',
          ];
        case 'stimulant':
          return [
            'Elevated movement velocity',
            'Increased motion frequency',
            'Heightened activity patterns',
          ];
        case 'depressant':
          return [
            'Reduced movement velocity',
            'Increased postural sway',
            'Slower reaction patterns',
          ];
        case 'cannabis':
          return [
            'Irregular movement patterns',
            'Variable timing detected',
            'Altered coordination observed',
          ];
        default:
          return ['Analysis complete'];
      }
    }

    final prediction = json['prediction'] ?? 'unknown';
    final confidence = (json['confidence'] ?? 0).toDouble();

    return ScanResult(
      scanId: (json['scan_id'] ?? json['id'] ?? '').toString(),
      prediction: prediction,
      confidence: confidence,
      probabilities: (() {
        final raw = json['probabilities'];
        if (raw == null) return <String, double>{};
        return Map<String, double>.from(
          (raw as Map).map((k, v) => MapEntry(k.toString(), (v as num).toDouble())),
        );
      })(),
      indicators: json['indicators'] != null
          ? List<String>.from(json['indicators'])
          : generateIndicators(prediction, confidence),
      detectionRate: (json['detection_rate'] ?? 1.0).toDouble(),
      framesAnalyzed: json['frames_analyzed'] ?? 0,
      duration: (json['duration_seconds'] ?? json['duration'] ?? 0).toDouble(),
      timestamp: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : (json['timestamp'] != null
              ? DateTime.parse(json['timestamp'])
              : DateTime.now()),
    );
  }

  String get predictionEmoji {
    switch (prediction.toLowerCase()) {
      case 'none':
        return '🟢';
      case 'stimulant':
        return '⚡';
      case 'depressant':
        return '😴';
      case 'cannabis':
        return '🌿';
      default:
        return '❓';
    }
  }

  String get predictionLabel {
    switch (prediction.toLowerCase()) {
      case 'none':
        return 'Normal';
      case 'stimulant':
        return 'Stimulant';
      case 'depressant':
        return 'Depressant';
      case 'cannabis':
        return 'Cannabis';
      default:
        return 'Unknown';
    }
  }

  bool get isNormal => prediction.toLowerCase() == 'none';
}
