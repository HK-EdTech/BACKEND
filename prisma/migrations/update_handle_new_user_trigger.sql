-- ================================================================
-- Update handle_new_user() Trigger Function
-- ================================================================
-- This script updates the trigger function to:
-- 1. Remove class_level from profiles table insertion
-- 2. Create role-specific profiles (student_profiles or teacher_profiles)
-- 3. Validate required fields based on role
-- ================================================================

-- Drop and recreate the trigger function
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
DECLARE
  role_uuid UUID;
  user_role TEXT;
  class_level_value TEXT;
BEGIN
  -- Get role from user metadata (default to 'student' if not provided)
  user_role := COALESCE(NEW.raw_user_meta_data->>'role', 'student');

  -- Validate role
  IF user_role NOT IN ('student', 'teacher', 'private_tutor') THEN
    RAISE EXCEPTION 'Invalid role: %. Must be student, teacher, or private_tutor', user_role;
  END IF;

  -- Get the role_id from the roles table
  SELECT id INTO role_uuid
  FROM public.roles
  WHERE name = user_role;

  -- If role not found, create it (for robustness)
  IF role_uuid IS NULL THEN
    INSERT INTO public.roles (id, name)
    VALUES (gen_random_uuid(), user_role)
    RETURNING id INTO role_uuid;
  END IF;

  -- Create base profile record (WITHOUT class_level)
  INSERT INTO public.profiles (
    id,
    first_name,
    surname,
    username,
    organization_id
  )
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'first_name', 'Unknown'),
    COALESCE(NEW.raw_user_meta_data->>'surname', 'User'),
    COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
    NULL
  );

  -- Create profile_roles relationship
  INSERT INTO public.profile_roles (profile_id, role_id)
  VALUES (NEW.id, role_uuid);

  -- Create role-specific profile
  IF user_role = 'student' THEN
    class_level_value := NEW.raw_user_meta_data->>'class_level';

    IF class_level_value IS NULL OR class_level_value = '' THEN
      RAISE EXCEPTION 'class_level is required in metadata for student role';
    END IF;

    INSERT INTO public.student_profiles (profile_id, level)
    VALUES (NEW.id, class_level_value);

  ELSIF user_role = 'teacher' THEN
    INSERT INTO public.teacher_profiles (profile_id, bio)
    VALUES (NEW.id, NULL);

  -- private_tutor: only base profile + role, no specialized table
  END IF;

  RETURN NEW;

EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'Error in handle_new_user for user %: %', NEW.id, SQLERRM;
    RAISE;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated;

-- Recreate trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- ================================================================
-- Verification Query
-- ================================================================
-- After running this script, you can verify the trigger exists with:
-- SELECT * FROM information_schema.triggers WHERE trigger_name = 'on_auth_user_created';
-- ================================================================
