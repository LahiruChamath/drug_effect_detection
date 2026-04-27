class User {
  final int? id;
  final String email;
  final String name;
  final String? token;
  final bool pushEnabled;
  final bool emailEnabled;
  final DateTime? createdAt;

  User({
    this.id,
    required this.email,
    required this.name,
    this.token,
    this.pushEnabled = true,
    this.emailEnabled = false,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json, {String? token}) {
    return User(
      id: json['id'],
      email: json['email'] ?? '',
      name: json['name'] ?? '',
      token: token ?? json['token'],
      pushEnabled: json['push_enabled'] ?? true,
      emailEnabled: json['email_enabled'] ?? false,
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'token': token,
      'push_enabled': pushEnabled,
      'email_enabled': emailEnabled,
    };
  }

  User copyWith({
    String? token,
    bool? pushEnabled,
    bool? emailEnabled,
  }) {
    return User(
      id: id,
      email: email,
      name: name,
      token: token ?? this.token,
      pushEnabled: pushEnabled ?? this.pushEnabled,
      emailEnabled: emailEnabled ?? this.emailEnabled,
      createdAt: createdAt,
    );
  }
}
