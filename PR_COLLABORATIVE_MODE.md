# Pull Request: Collaborative Mode Feature

## Summary
This PR introduces a collaborative mode for AdventureLogs that enables shared editing of public content across users. When enabled via `COLLABORATIVE_MODE=true`, any authenticated user can edit public locations, add visits, upload images, and more.

## Features

### Core Functionality
- **Public Location Editing**: Any authenticated user can edit public locations
- **Per-User Attribution**: Visits, images, and attachments are attributed to their creator/uploader
- **Ownership Restrictions**: Users can only delete their own content (visits, images, attachments)
- **Soft-Delete**: Images and attachments are soft-deleted in collaborative mode, allowing recovery

### Audit Logging
- All changes are tracked with user attribution
- Models logged: Location, Collection, Category, Visit, ContentImage, ContentAttachment, Note, Transportation, Lodging
- History panel displays all modifications on location detail page

### Revert Functionality
- Revert field updates (restore old values)
- Revert image/attachment creation (soft-delete)
- Revert image/attachment deletion (restore from soft-delete)
- Permission checks: only creator, location owner, or staff can revert

## Technical Changes

### Backend
- `permissions.py`: Updated `IsOwnerOrSharedWithFullAccess` for collaborative mode
- `permissions.py`: Added `ContentImagePermission` for image/attachment deletion
- `signals.py`: Audit logging via Django signals
- `middleware.py`: `AuditUserMiddleware` captures current user for logging
- `models.py`: Soft-delete fields on `ContentImage` and `ContentAttachment`
- `serializers.py`: Added `user_username` to Visit, ContentImage, Attachment serializers
- Views updated: location_view, visit_view, location_image_view, attachment_view, note_view, transportation_view, lodging_view

### Frontend
- `HistoryPanel.svelte`: Display audit history with revert buttons
- `LocationVisits.svelte`: Show who added each visit, restrict edit/delete to owner
- `+page.svelte`: Show uploader username on images

### Database Migrations
- `0072_visit_user.py`: Add user field to Visit model
- `0073_populate_visit_users.py`: Populate existing visits with location owner
- `0074_soft_delete_fields.py`: Add soft-delete fields to ContentImage and ContentAttachment

## Configuration
Set the environment variable to enable:
```
COLLABORATIVE_MODE=true
```

## Testing
Comprehensive test suite added: `backend/server/adventures/tests/test_collaborative_mode.py`
- 41 test methods across 22 test classes
- Permission tests
- Audit logging tests
- Revert functionality tests
- Ownership attribution tests
- Edge case tests

Run tests with:
```bash
cd backend/server
python manage.py test adventures.tests.test_collaborative_mode
```

## Permission Matrix

| Content Type | Create | Read | Update | Delete |
|--------------|--------|------|--------|--------|
| Public Location | Any auth user | Anyone | Any auth user | Owner only |
| Visit | Any auth user | Anyone | Creator only | Creator only |
| Image | Any auth user | Anyone | - | Uploader only |
| Attachment | Any auth user | Anyone | - | Uploader only |

## Breaking Changes
None. Feature is opt-in via environment variable.

## Checklist
- [x] Backend permissions implemented
- [x] Audit logging implemented
- [x] Revert functionality implemented
- [x] Frontend UI updated
- [x] Tests written
- [x] Migrations created
- [x] Documentation updated (MEMORY.md)
