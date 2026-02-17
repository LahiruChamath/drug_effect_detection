class User {
  final String email;
  final String name;
  final String? token;

  User({
    required this.email,
    required this.name,
    this.token,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      email: json['email'] ?? '',
      name: json['name'] ?? '',
      token: json['token'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'email': email,
      'name': name,
      'token': token,
    };
  }
}
