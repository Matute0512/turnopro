# TurnoPro 📅

Un gestor de turnos y citas full-stack de grado empresarial, diseñado con Arquitectura Limpia, validación matemática de prevención de colisiones y altos estándares de seguridad (OWASP).

## 🚀 Características Principales

- **Prevención de Overbooking:** Algoritmo matemático asíncrono de intersección de rangos temporales `(StartA < EndB) AND (EndA > StartB)` para garantizar exclusividad de agenda.
- **Seguridad OWASP (Zero Trust):** Autenticación mediante JSON Web Tokens (JWT). Uso estricto de Access Tokens en memoria y Refresh Tokens aislados en cookies `HttpOnly` para mitigar ataques XSS y CSRF.
- **Arquitectura Feature-First:** Frontend móvil/web encapsulado por funcionalidades, con inyección de dependencias reactiva para un control de estado predecible y Auth Guards de enrutamiento.
- **API Altamente Concurrente:** Backend de alto rendimiento que previene problemas de latencia y cargas (N+1) mediante Eager Loading (`joinedload`).

## 🛠️ Stack Tecnológico

**Frontend (Client):**

- **Framework:** Flutter & Dart
- **State Management:** Riverpod 2.x (NotifierProvider)
- **Networking:** Dio (con interceptores JWT y mitigación 401)
- **Routing & Auth Guard:** GoRouter
- **Security:** Flutter Secure Storage (Keystore/Keychain)

**Backend (Server):**

- **Core:** Python 3.10 & FastAPI
- **Base de Datos:** PostgreSQL con driver asíncrono (`asyncpg`)
- **ORM:** SQLAlchemy 2.0 & Alembic (Migraciones)
- **Validación de Contratos:** Pydantic
- **Criptografía:** Bcrypt nativo

## 🐳 Despliegue Local (Docker)

El proyecto está completamente contenerizado, garantizando paridad entre los entornos de desarrollo y producción.

1. Clona el repositorio:

```bash
git clone [https://github.com/tu-usuario/turnopro.git](https://github.com/tu-usuario/turnopro.git)
cd turnopro
```

2. Levanta la infraestructura (Base de Datos + API):

```bash
docker compose up --build -d
```

La API estará disponible en [[http://localhost:8000/docs](http://localhost:8000/docs)] (Swagger UI).

3. Ejecuta el Frontend (Emulador o Web):

```bash
cd frontend
flutter clean
flutter pub get
flutter run
```

## 🧪 Testing y Calidad

La capa de servicios del backend cuenta con una suite de pruebas End-to-End (E2E) aisladas utilizando una base de datos SQLite en memoria (RAM) gestionada por ``aiosqlite`` y clientes asíncronos ``httpx``, garantizando que las reglas de negocio críticas mantengan su integridad en cada refactorización.

```bash
cd backend
python -m pytest -v
```

## 👨‍💻 Autor

Estudiante de Ingeniería en Informática (UADE)

Buenos Aires, Argentina

LinkedIn | GitHub
