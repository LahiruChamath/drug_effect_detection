class User {
  final int? id;
  final String email;
  final String name;
  final String? token;
  final DateTime? createdAt;

  User({
    this.id,
    required this.email,
    required this.name,
    this.token,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json, {String? token}) {
    return User(
      id: json['id'],
      email: json['email'] ?? '',
      name: json['name'] ?? '',
      token: token ?? json['token'],
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
    };
  }

  User copyWith({String? token}) {
    return User(
      id: id,
      email: email,
      name: name,
      token: token ?? this.token,
      createdAt: createdAt,
    );
  }
}
