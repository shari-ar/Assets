# User Roles & Permissions

## Overview

The **Assets** platform implements a robust **role-based access control (RBAC)** system to ensure that users have access only to authorized functionality. This guide explains the available roles, permission hierarchies, and enforcement mechanisms within the backend and frontend applications.

---

## Goals

- Protect sensitive operations from unauthorized access.
- Simplify permission management for users and admins.
- Support future scalability (e.g., team-based or organization-based roles).
- Enforce the principle of least privilege.

---

## Core Roles

| Role      | Description                                  | Typical Actions                                                  |
| --------- | -------------------------------------------- | ---------------------------------------------------------------- |
| **Admin** | Platform administrator with full privileges. | Manage users and generate reports.                               |
| **User**  | Standard authenticated user.                 | Create and manage their own tickets, use wallet, view reports.   |

---

## Role Hierarchy

```
Admin
 └── User
```

- **Admins** have read access to all resources.
- **Users** have access only to their own data and limited public endpoints.
- Future roles (e.g., `moderator`, `auditor`) can extend this hierarchy.

---

## Permission Matrix

| Module              | Action                   | User | Admin |
| ------------------- | ------------------------ | ---- | ----- |
| **Authentication**  | Register/Login           | ✅  | ✅    |
| **Tickets**         | Create/Update/Delete Own | ✅  | ✅    |
| **Tickets**         | Read Any                 | ❌  | ✅    |
| **Wallet**          | View/Manage Own          | ✅  | ✅    |
| **Wallet**          | Reads Others’ Wallets    | ❌  | ✅    |
| **Reports**         | View Personal Reports    | ✅  | ✅    |
| **Reports**         | Access All Reports       | ❌  | ✅    |
| **Notifications**   | Receive                  | ✅  | ✅    |
| **Notifications**   | Broadcast                | ❌  | ✅    |
| **Admin Dashboard** | Access                   | ❌  | ✅    |

✅ = Allowed | ❌ = Restricted

---

## API Role Enforcement

All API routes define permission decorators or dependencies.

| Decorator                 | Description                               |
| ------------------------- | ----------------------------------------- |
| `@login_required`         | Requires authentication.                  |
| `@admin_required`         | Restricts access to admin-only endpoints. |

---

## Admin Dashboard Permissions

The admin dashboard is accessible only to users with the `admin` role.  
It allows the following operations:

- View all users and wallets.
- Generate and export financial reports.
- Broadcast notifications to all users.

---

## Security Considerations

- Tokens include user role claims (`role=admin` or `role=user`).
- Backend authorization always takes precedence over frontend visibility.
- Sensitive endpoints enforce both **JWT validation** and **role checks**.
- Logs include user ID and role for every API call.
- Attempted access violations are recorded for audit.

---

## Future Role Extensions

| Planned Role      | Description                                             |
| ----------------- | ------------------------------------------------------- |
| **Moderator**     | Manage and verify asset listings.                       |
| **Auditor**       | Read-only access to financial reports and logs.         |
| **Support Agent** | Handle ticket and user inquiries via support dashboard. |

---

## Testing Permissions

**Example Tests:**

```python
def test_user_cannot_access_admin_endpoints(client, user):
    client.force_authenticate(user)
    response = client.get("/api/v1/admin/reports/")
    assert response.status_code == 403

def test_admin_can_access_reports(client, admin_user):
    client.force_authenticate(admin_user)
    response = client.get("/api/v1/admin/reports/")
    assert response.status_code == 200
```

---

## Summary

| Component              | Enforcement Location       |
| ---------------------- | -------------------------- |
| **JWT & OAuth Tokens** | Authentication Layer       |
| **Role Checks**        | Middleware and Endpoints   |
| **UI Restrictions**    | Frontend Components        |
| **Database Filters**   | Querysets and Repositories |

Together, these ensure that data access is consistent, secure, and auditable across the entire system.
