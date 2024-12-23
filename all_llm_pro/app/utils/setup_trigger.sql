-- 1. 트리거가 호출할 함수 생성
CREATE OR REPLACE FUNCTION notify_unchecked_maf_chk() RETURNS TRIGGER AS $$
DECLARE
    unchecked_idx text;
BEGIN
    -- maf_chk가 false이고 maf_idx가 NULL이 아닌 경우에만 알림을 전송
    IF NEW.maf_chk = false AND NEW.maf_idx IS NOT NULL THEN
        unchecked_idx := NEW.maf_idx::text; -- maf_idx 값을 가져옴
        PERFORM pg_notify('unchecked_maf_chk', unchecked_idx); -- 알림 전송
    ELSE
        RAISE NOTICE 'No notification sent. Condition not met: maf_chk=% or maf_idx IS NULL', NEW.maf_chk;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. 트리거 생성
DROP TRIGGER IF EXISTS maf_chk_trigger ON mw_audio_analysis;
CREATE TRIGGER maf_chk_trigger
AFTER INSERT OR UPDATE ON mw_audio_analysis
FOR EACH ROW
EXECUTE FUNCTION notify_unchecked_maf_chk();
