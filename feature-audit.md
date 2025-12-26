# Аудит Кодовой Базы

## Функция: Аутентификация Пользователей — Stable

**User Story:** Как пользователь, я хочу регистрироваться и входить в систему с помощью email и пароля, чтобы получить доступ к своему аккаунту. Также входить с помощью Google и VK ID

**Описание:** Реализует регистрацию пользователей, вход по email/паролю, генерацию JWT-токенов, подтверждение email, интеграцию с VK. Поддерживает роли пользователей.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/routers/auth.py | source | Синтаксис OK; содержит обработку ошибок; тесты существуют — Pass (на основе структуры); Покрытие: Covered |
| app/models/user.py | source | Синтаксис OK; модель пользователя с хэшированием пароля; тесты существуют — Pass; Покрытие: Covered |
| app/services/auth/jwt.py | source | Синтаксис OK; генерация и декодирование токенов; тесты существуют — Pass; Покрытие: Covered |
| app/services/auth/password.py | source | Синтаксис OK; валидация и хэширование паролей; тесты существуют — Pass; Покрытие: Covered |
| app/services/auth/email.py | source | Синтаксис OK; отправка email для подтверждения; тесты существуют — Pass; Покрытие: Covered |
| app/services/auth/vk.py | source | Синтаксис OK; интеграция с VK OAuth; тесты отсутствуют; Покрытие: Not covered |
| app/schemas/user.py | source | Синтаксис OK; схемы для создания и логина пользователей; тесты существуют — Pass; Покрытие: Covered |
| app/utils/auth.py | source | Синтаксис OK; утилиты для получения текущего пользователя; тесты существуют — Pass; Покрытие: Covered |
| tests/test_users.py | test | Тесты для регистрации и логина; Один тест Fall (logout); Покрытие: Covered |

**Issues & Recommendations:**
- (Medium) Исправить тест test_login_and_logout: refresh token остается валидным после logout (проверить логику в app/utils/redis.py или auth роутере).
- (Medium) Проверить работоспособность VK OAuth интеграции (app/services/auth/vk.py), так как тесты отсутствуют и интеграция может не работать.
- (Medium) Добавить rate limiting для предотвращения brute-force атак на логин (в app/routers/auth.py добавить TODO для реализации).

## Функция: Управление Профилями Пользователей — Stable

**User Story:** Как пользователь, я хочу управлять своим профилем, включая обновление информации и фото, чтобы поддерживать актуальные данные.

**Описание:** Позволяет получает публичный профиль по username, обновляет личную информацию, меняет пароль, загружает фото.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/routers/user.py | source | Синтаксис OK; эндпоинты для профиля и обновления; тесты существуют — Pass; Покрытие: Covered |
| app/models/user.py | source | Синтаксис OK; модель с полями профиля; тесты существуют — Pass; Покрытие: Covered |
| app/schemas/user.py | source | Синтаксис OK; схемы для обновления профиля; тесты существуют — Pass; Покрытие: Covered |
| app/utils/auth.py | source | Синтаксис OK; зависимости для аутентификации; тесты существуют — Pass; Покрытие: Covered |
| tests/test_users.py | test | Тесты для профилей; Pass; Покрытие: Covered |

**Issues & Recommendations:**
- (Low) Добавить валидацию размера фото при загрузке (в app/routers/user.py ограничить размер файла).

## Функция: Регистрация и Управление Организациями — To fix

**User Story:** Как владелец бизнеса, я хочу регистрировать свою организацию и управлять ею, чтобы предлагать акции и скидки клиентам.

**Описание:** Регистрация организаций с типом, адресом, скидками; управление местами (places), связанными с организациями; геокодирование адресов.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/routers/organization.py | source | Синтаксис OK; эндпоинты для регистрации и управления; тесты существуют — Pass; Покрытие: Covered |
| app/models/organization.py | source | Синтаксис OK; модель организации с типами и скидками; тесты существуют — Pass; Покрытие: Covered |
| app/schemas/organization.py | source | Синтаксис OK; схемы для создания и обновления; тесты существуют — Pass; Покрытие: Covered |
| app/services/geocoder.py | source | Синтаксис OK; геокодирование с Yandex API; тесты существуют — Pass; Покрытие: Covered |
| app/utils/auth.py | source | Синтаксис OK; проверка админа организации; тесты существуют — Pass; Покрытие: Covered |
| tests/test_organizations.py | test | Тесты для организаций; Pass; Покрытие: Covered |
| tests/test_places.py | test | Тесты для places; Fall из-за 403 Forbidden от Yandex API; Покрытие: Covered |

**Issues & Recommendations:**
- (High) Исправить API-ключ Yandex: тесты падают с 403 Forbidden (обновить ключ в settings.py или использовать переменные окружения).
- (Medium) Обеспечить безопасность API-ключа Yandex в settings.py (не хардкодить, использовать переменные окружения).

## Функция: Создание и Управление Акциями (Goals) — Stable

**User Story:** Как организация, я хочу создавать и управлять акциями (goals), чтобы привлекать клиентов предложениями.

**Описание:** Создание акций с датами, временем, адресом, описанием, призами; обновление и получение акций; валидация дат и времени.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/routers/goal.py | source | Синтаксис OK; эндпоинты CRUD для goals; тесты существуют — Pass; Покрытие: Covered |
| app/models/goal.py | source | Синтаксис OK; модель goal с связями; тесты существуют — Pass; Покрытие: Covered |
| app/schemas/goal.py | source | Синтаксис OK; схемы для создания и обновления; тесты существуют — Pass; Покрытие: Covered |
| app/utils/auth.py | source | Синтаксис OK; проверка прав; тесты существуют — Pass; Покрытие: Covered |
| tests/test_goals.py | test | Тесты для goals; Pass; Покрытие: Covered |

**Issues & Recommendations:**
- (Low) Добавить валидацию изображений контента (в app/routers/goal.py проверить тип и размер файлов).

## Функция: Создание и Управление Отзывами (Stories) — To fix

**User Story:** Как клиент, я хочу оставлять отзывы (stories) после посещения заведения, отсканировав QR-код или голс организации, получив скидку при оплате, чтобы поделиться опытом.

**Описание:** Создание отзывов с текстом, контентом (фото); модерация; связь с goal или organization; получение скидки после сканирования. Полный CRUD: создание, получение, обновление, удаление; модерация админами; установка позиций в избранных.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/routers/story.py | source | Синтаксис OK; полный CRUD эндпоинты для stories; тесты существуют — Fall; Покрытие: Covered |
| app/models/story.py | source | Синтаксис OK; модель с модерацией; тесты существуют — Fall; Покрытие: Covered |
| app/schemas/story.py | source | Синтаксис OK; схемы для создания; тесты существуют — Fall; Покрытие: Covered |
| app/models/discount.py | source | Синтаксис OK; модель скидок; тесты существуют — Fall; Покрытие: Covered |
| app/utils/auth.py | source | Синтаксис OK; аутентификация; тесты существуют — Fall; Покрытие: Covered |
| tests/test_stories.py | test | Тесты для stories; Множество тестов Fall (ValueError, AssertionError с "История не найдена"); Покрытие: Covered |

**Issues & Recommendations:**
- (High) Исправить тесты stories: ValueError в test_create_story (проблема с итерацией); AssertionError в тестах с "История не найдена" (проверить создание и получение в тестах).
- (High) Исправить test_admin_change_story_moderation_state: ошибка с moderation state (проверить логику в роутере).
- (Medium) Модерация stories реализована (эндпоинты для админа), но тесты падают — исправить после фикса основных ошибок.

## Функция: Генерация Баркодов — To fix

**User Story:** Как пользователь, я хочу генерировать баркоды для акций, чтобы сканировать их в заведениях и получать скидки.

**Описание:** Генерация SVG-баркодов для goals с уникальными значениями; хранение в базе как codes.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/routers/barcode.py | source | Синтаксис OK; генерация баркодов; тесты отсутствуют; Покрытие: Not covered |
| app/models/code.py | source | Синтаксис OK; модель codes; тесты отсутствуют; Покрытие: Not covered |
| app/schemas/code.py | source | Синтаксис OK; схемы для codes; тесты отсутствуют; Покрытие: Not covered |
| tests/test_loyalty_system.py | test | Пустой файл; тесты отсутствуют; Покрытие: Not covered |

**Issues & Recommendations:**
- (High) Заполнить tests/test_loyalty_system.py полными тестами для генерации баркодов и применения скидок.

## Функция: Поиск Мест — To fix

**User Story:** Как пользователь, я хочу искать места (организации) по названию, типу, наличию акций или скидок, чтобы найти подходящие заведения.

**Описание:** Поиск организаций с фильтрами; возврат с геолокацией.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/routers/search.py | source | Синтаксис OK; эндпоинт поиска; тесты существуют — Fall; Покрытие: Covered |
| app/models/organization.py | source | Синтаксис OK; модель Place; тесты существуют — Fall; Покрытие: Covered |
| app/routers/organization.py | source | Синтаксис OK; утилиты для локации; тесты существуют — Fall; Покрытие: Covered |
| app/services/geocoder.py | source | Синтаксис OK; геокодирование; тесты существуют — Fall; Покрытие: Covered |
| tests/test_search.py | test | Тесты для поиска; Fall с 500 вместо 200; Покрытие: Covered |

**Issues & Recommendations:**
- (High) Исправить test_search_places: возвращает 500 вместо 200 (проверить логику в app/routers/search.py, возможно, проблема с геокодированием или фильтрами).
- (Low) Оптимизировать поиск с индексами в базе (добавить индексы на поля поиска в app/models/organization.py).

## Функция: Система Скидок — To fix

**User Story:** Как организация, я хочу предоставлять персонализированные скидки клиентам на основе их активности, чтобы поощрять повторные посещения.

**Описание:** Управление скидками для пользователей в организациях; накопление скидок.

**Файлы:**
| Путь | Тип | Заметки |
|------|-----|---------|
| app/models/discount.py | source | Синтаксис OK; модель скидок; тесты отсутствуют; Покрытие: Not covered |
| app/models/organization.py | source | Синтаксис OK; поля скидок; тесты существуют — Предположительно Pass; Покрытие: Partially covered |
| tests/test_loyalty_system.py | test | Пустой файл; тесты отсутствуют; Покрытие: Not covered |

**Issues & Recommendations:**
- (High) Реализовать тесты в tests/test_loyalty_system.py для создания и применения скидок.
- (Medium) Добавить логику расчета скидок на основе шагов (step_amount, days_to_step_back в app/models/organization.py).

## Summary

Общее количество функций: 8  
Stable: 3  
Untested: 0  
To fix: 5  

**Top 10 issues:**  
1. (High) Исправить тесты stories: ValueError и AssertionError с "История не найдена".  
2. (High) Исправить API-ключ Yandex: 403 Forbidden в тестах places.  
3. (High) Заполнить tests/test_loyalty_system.py тестами для баркодов и скидок.  
4. (High) Исправить test_search_places: 500 вместо 200.  
5. (High) Исправить test_admin_change_story_moderation_state.  
6. (Medium) Проверить работоспособность VK OAuth интеграции.  
7. (Medium) Исправить test_login_and_logout: refresh token после logout.  
8. (Medium) Обеспечить безопасность API-ключа Yandex.  
9. (Low) Добавить валидацию размера фото.  
10. (Low) Оптимизировать поиск с индексами.  

**Prioritized fixes:**  
1. Исправить API-ключ Yandex и тесты places (зависит от внешнего сервиса).  
2. Исправить тесты stories (ValueError и получение историй).  
3. Заполнить tests/test_loyalty_system.py полными тестами.  
4. Исправить test_search_places.  
5. Исправить test_login_and_logout.  
6. Проверить и исправить VK OAuth интеграцию.  
7. Переместить Yandex API ключ в переменные окружения.  
8. Добавить валидации для загрузки файлов.  
9. Добавить индексы для поиска.  
10. Реализовать rate limiting для логина.