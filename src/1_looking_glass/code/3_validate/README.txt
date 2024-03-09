This directory we check the websites that are not decided by the previous process, and try to decide them by checking the looking glass routers.

1. Run `0_dump_to_readable.py` first to get the readable list of undecided websites (tbd).

<<<<<<< HEAD
2. After process all the tbd routers,  run `1_merge_into_final.py` to merge the result into good result.
=======
2. After process all the tbd routers,  run `1_merge_into_prev.py` to merge the result into good result.

3. Run `2_validate_routers.py` to validate the looking glass routers, and generate the suspicious routers.

4. After checking the suspicious routers, run `3_merge_to_final.py` to get the final list of routers.
>>>>>>> origin/HEAD
