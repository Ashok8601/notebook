# 📓 Notebook API Documentation

Ek robust Flask-based REST API jo notes ko manage karne, export karne aur secure account operations ke liye design ki gayi hai.

## 🚀 API Reference

### 1. User Authentication
| Endpoint | Method | JSON Body / Payload | Description |
| :--- | :--- | :--- | :--- |
| `/signup` | `POST` | `{"name": "...", "email": "...", "password": "...", "dob": "..."}` | Naya account create karein. |
| `/login` | `POST` | `{"email": "...", "password": "..."}` | Login karke session establish karein. |
| `/update_password`| `PUT` | `{"email": "...", "old_password": "...", "password": "..."}` | Password change karein. |
| `/delete_account` | `POST` | None | Account ko 30 din ke deletion queue mein daalein. |
| `/recover_account`| `POST` | `{"email": "...", "password": "..."}` | Account ko delete hone se pehle restore karein. |

### 2. Profile Management
| Endpoint | Method | Form Data / JSON | Description |
| :--- | :--- | :--- | :--- |
| `/profile_dashboard`| `GET` | None | User profile ki saari details fetch karein. |
| `/update_user/<id>` | `PUT` | `name, email, dob, mobile, username, secret_key, photo` | Profile update aur image upload. |

### 3. Notebook Operations
| Endpoint | Method | JSON Body / Payload | Description |
| :--- | :--- | :--- | :--- |
| `/create_note` | `POST` | `{"title": "...", "content": "..."}` | Nayi note banayein. |
| `/notes` | `GET` | None | Saari active notes ki list lein. |
| `/update_note/<id>` | `PUT` | `{"title": "...", "content": "..."}` | Specific note edit karein. |
| `/search` | `POST` | `{"query": "your_search_text"}` | Title/Content mein keyword search karein. |
| `/filter` | `POST` | `{"method": "latest" / "oldest" / "title"}` | Notes ko sort karein. |

### 4. Trash & Recovery
| Endpoint | Method | JSON Body / Payload | Description |
| :--- | :--- | :--- | :--- |
| `/move_to_trash/<id>` | `PUT` | None | Note ko trash mein bhejein. |
| `/trash` | `GET` | None | Trashed notes ki list dekhein. |
| `/restore_note/<id>` | `PUT` | None | Note ko trash se wapas layein. |

### 5. Export & Sharing
| Endpoint | Method | Query Params | Description |
| :--- | :--- | :--- | :--- |
| `/export_note/<id>` | `GET` | `?type=pdf` OR `?type=docx` | Note ko specific format mein download karein. |
| `/share_note/<id>` | `POST` | `{"email": "receiver@mail.com"}` | Note ko email ke zariye share karein. |

---

## 🏗 Database Schema Overview
Samajhne ke liye ki data kaise relate ho raha hai, neeche architecture dekhein:



## 🛠 Setup & Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install flask reportlab python-docx Flask-APScheduler
   
