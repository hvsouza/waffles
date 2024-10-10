#!/bin/bash

type=${1:-purity}
ot=${2:--r}
maxprocess=${3:-3}

if [ "$ot" != -t ]; then
    runlist=$( tail -n +2 runlists/${type}_runs.csv | cut -d , -f 1 )
else
    runlist=$( tail -n +2 runlists/${type}_runs.csv | cut -d , -f 5 | sort | uniq )
    ot=-t
fi

echo ${runlist[@]} | xargs -P${maxprocess} -n1 bash -c 'python extract_selection.py --runs "$0" '${ot}' -rl '${type}' -ch 11114 11116 -f'

echo ${runlist[@]} | xargs -P${maxprocess} -n1 bash -c 'python extract_selection.py --runs "$0" '${ot}' -rl '${type}' -ch 11225 11227 -f'

# Not good...
# i=0
# for r in ${runlist[@]}; do
#     ((i=i%maxprocess)); ((i++==0)) && wait
#     python extract_selection.py --runs $r $ot -rl ${type} -ch 11114 11116 -f  &
# done

wait && echo "All done..."
