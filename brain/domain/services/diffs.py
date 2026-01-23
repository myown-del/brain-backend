import diff_match_patch as dmp_module

from brain.domain.value_objects import LinkInterval


def apply_patch(text: str, patch_text: str) -> str:
    """Apply a diff-match-patch string to the original text and return the result."""
    dmp = dmp_module.diff_match_patch()
    patches = dmp.patch_fromText(patch_text)
    new_text, _ = dmp.patch_apply(patches, text)
    return new_text


def get_patches_str(text1: str, text2: str) -> str:
    """Produce the serialized patch instructions needed to transform text1 into text2."""
    dmp = dmp_module.diff_match_patch()
    patches = dmp.patch_make(text1, text2)
    return dmp.patch_toText(patches)


def get_diffs(text1: str, text2: str) -> list[tuple[int, int]]:
    """Return diff tuples describing how text2 differs from text1."""
    dmp = dmp_module.diff_match_patch()
    diffs = dmp.diff_main(text1, text2)
    dmp.diff_cleanupSemantic(diffs)
    
    return diffs



def check_if_ranges_touched(
    old_text_len: int,
    diffs: list[tuple[int, str]],
    protected_ranges: list[LinkInterval],
) -> bool:
    """
    Checks if any of the diffs overlap with the protected ranges in the **old** text.
    
    diffs: list of (op, text) from diff_main.
            0 = EQUAL
            1 = INSERT
           -1 = DELETE
    """
    current_pos = 0
    
    # Sort ranges by start just in case
    sorted_ranges = sorted(protected_ranges)
    
    for op, text in diffs:
        length = len(text)
        
        if op == 0:  # EQUAL
            # This segment is unchanged.
            # We just advance position.
            current_pos += length
            
        elif op == -1: # DELETE
            # This segment existed in old text (at current_pos) but is removed.
            # Check if this removal overlaps with any protected range.
            # Range: [current_pos, current_pos + length)
            del_start = current_pos
            del_end = current_pos + length
            
            for interval in sorted_ranges:
                # Check overlap
                if max(del_start, interval.start) < min(del_end, interval.end):
                    return True
            
            current_pos += length
            
        elif op == 1: # INSERT
            # This segment is new. It sits at current_pos in old text (between characters).
            # It implies a change happened AT this position.
            # If we insert inside a link "[[li|nk]]" -> "[[liINSERT|nk]]", 
            # the link text changes.
            # So insertion at X touches a range if start < X < end.
            
            ins_pos = current_pos
            for interval in sorted_ranges:
                if interval.start < ins_pos < interval.end:
                    return True
                    
            # Insert doesn't consume old text, so current_pos stays same.

    return False
