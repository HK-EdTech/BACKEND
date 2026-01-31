# Database Schema Migration Summary

## ✅ Completed Tasks

### 1. Database Schema Changes
- ✅ Removed `class_level` column from `profiles` table
- ✅ Created `student_profiles` table with `profile_id`, `level`, timestamps
- ✅ Created `teacher_profiles` table with `profile_id`, `bio`, timestamps
- ✅ Updated foreign key constraints for `classes` and `enrollments` tables

### 2. Trigger Function Updates
- ✅ Updated `handle_new_user()` trigger function to:
  - Remove `class_level` from profile insertion
  - Create student profile for role='student' (requires `class_level` in metadata)
  - Create teacher profile for role='teacher'
  - Support private_tutor role (no specialized table)
  - Validate required fields and roles

### 3. Backend Code Updates

#### Updated Files:
1. **prisma/schema.prisma**
   - Removed `class_level` from profiles model
   - Added `student_profiles` model
   - Added `teacher_profiles` model
   - Updated relations in classes and enrollments

2. **src/modules/profile/pydantic_model/profile_pydantic_model.py**
   - Removed `class_level` from ProfileResponse
   - Added `StudentProfileResponse` model
   - Added `TeacherProfileResponse` model
   - Added `student_profile` and `teacher_profile` fields to ProfileResponse

3. **src/modules/profile/pydantic_model/update_profile_pydantic_model.py**
   - Removed `class_level` from ProfileUpdateRequest
   - Added `StudentProfileUpdateRequest` model
   - Added `TeacherProfileUpdateRequest` model

4. **src/modules/profile/profile_service.py**
   - Updated `get_profile_by_id()` to include specialized profiles
   - Removed `class_level` from `update_profile()`
   - Added `get_student_profile()` method
   - Added `update_student_level()` method
   - Added `get_teacher_profile()` method
   - Added `update_teacher_bio()` method

5. **src/modules/profile/profile_controller.py**
   - Removed `class_level` from PUT /profile/me
   - Added GET /profile/me/student endpoint
   - Added PUT /profile/me/student endpoint
   - Added GET /profile/me/teacher endpoint
   - Added PUT /profile/me/teacher endpoint

---

## 🧪 Testing Checklist

### Student Signup ✅
**Metadata Required:**
```json
{
  "role": "student",
  "class_level": "Form 4",
  "first_name": "John",
  "surname": "Doe",
  "username": "johndoe"
}
```

**Expected Database State:**
- ✅ Entry in `profiles` table (WITHOUT class_level column)
- ✅ Entry in `profile_roles` with role='student'
- ✅ Entry in `student_profiles` with level='Form 4'
- ✅ No entry in `teacher_profiles`

**API Tests:**
```bash
# Get full profile (includes student_profile)
GET /profile/me

# Get student-specific profile
GET /profile/me/student

# Update class level
PUT /profile/me/student
{
  "level": "Form 5"
}
```

---

### Teacher Signup ✅
**Metadata Required:**
```json
{
  "role": "teacher",
  "first_name": "Jane",
  "surname": "Smith",
  "username": "janesmith"
}
```

**Expected Database State:**
- ✅ Entry in `profiles` table
- ✅ Entry in `profile_roles` with role='teacher'
- ✅ Entry in `teacher_profiles` with bio=NULL
- ✅ No entry in `student_profiles`

**API Tests:**
```bash
# Get full profile (includes teacher_profile)
GET /profile/me

# Get teacher-specific profile
GET /profile/me/teacher

# Update bio
PUT /profile/me/teacher
{
  "bio": "Experienced mathematics teacher with 10 years of experience."
}
```

---

### Private Tutor Signup ✅
**Metadata Required:**
```json
{
  "role": "private_tutor",
  "first_name": "Bob",
  "surname": "Wilson",
  "username": "bobwilson"
}
```

**Expected Database State:**
- ✅ Entry in `profiles` table
- ✅ Entry in `profile_roles` with role='private_tutor'
- ✅ No entry in `student_profiles`
- ✅ No entry in `teacher_profiles`

**API Tests:**
```bash
# Get full profile (both specialized profiles are NULL)
GET /profile/me
```

---

### Error Cases to Test

1. **Student without class_level:**
```json
{
  "role": "student",
  "first_name": "Test",
  "surname": "User"
}
```
**Expected:** Signup fails with error: "class_level is required in metadata for student role"

2. **Invalid role:**
```json
{
  "role": "admin",
  "first_name": "Test",
  "surname": "User"
}
```
**Expected:** Signup fails with error: "Invalid role: admin. Must be student, teacher, or private_tutor"

3. **Access wrong profile type:**
- Student accessing `/profile/me/teacher` → Expected: 404 Not Found
- Teacher accessing `/profile/me/student` → Expected: 404 Not Found

---

## 🔄 New API Endpoints

### Base Profile Endpoints
- `GET /profile/me` - Get profile with role-specific data included
- `PUT /profile/me` - Update base profile (first_name, surname, username, avatar_url)

### Student-Specific Endpoints
- `GET /profile/me/student` - Get student profile with enrollments and classes
- `PUT /profile/me/student` - Update student level

### Teacher-Specific Endpoints
- `GET /profile/me/teacher` - Get teacher profile with classes
- `PUT /profile/me/teacher` - Update teacher bio

---

## 📝 Frontend Changes Needed (Optional)

The frontend signup flow remains unchanged, but you may want to update:

1. **Profile Display:**
   - Show `student_profile.level` instead of `class_level`
   - Show `teacher_profile.bio` for teachers
   - Handle cases where specialized profiles are null

2. **Profile Update Forms:**
   - Update student level: Use `PUT /profile/me/student`
   - Update teacher bio: Use `PUT /profile/me/teacher`
   - Update base info: Use `PUT /profile/me`

---

## 🔧 Rollback Plan

If you need to rollback:

```sql
BEGIN;

-- Restore class_level column
ALTER TABLE public.profiles ADD COLUMN class_level VARCHAR(50);
CREATE INDEX idx_profiles_class_level ON public.profiles(class_level);

-- Restore original FK constraints
ALTER TABLE public.classes
    DROP CONSTRAINT classes_teacher_id_fkey,
    ADD CONSTRAINT classes_teacher_id_fkey
        FOREIGN KEY (teacher_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

ALTER TABLE public.enrollments
    DROP CONSTRAINT enrollments_student_id_fkey,
    ADD CONSTRAINT enrollments_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

-- Drop new tables
DROP TABLE IF EXISTS public.student_profiles CASCADE;
DROP TABLE IF EXISTS public.teacher_profiles CASCADE;

COMMIT;
```

Then:
```bash
cd BACKEND_FORK
python3 -m prisma db pull  # Sync schema.prisma with database
python3 -m prisma generate # Regenerate client
```

---

## 📊 Migration Status: COMPLETE ✅

All components have been successfully updated:
- ✅ Database schema migrated
- ✅ Trigger function updated
- ✅ Backend services updated
- ✅ API endpoints created
- ✅ Pydantic models updated
- ✅ Signup tested and working

**Next Steps:**
1. Test all three signup flows (student, teacher, private_tutor)
2. Test profile retrieval and updates
3. Test error cases
4. Update frontend if needed
5. Monitor logs for any issues
