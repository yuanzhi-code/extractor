#!/bin/bash

URLS=(
    https://mp.weixin.qq.com/s/yzfNRAJyITdHN4xskNCSWg
    https://mp.weixin.qq.com/s/MH18fZ5XghUPEd1Dsy1TXQ
    "https://mp.weixin.qq.com/s?__biz=Mzg3MTk3NzYzNw==&mid=2247496063&idx=1&sn=2eb1496c16b321f264090288738aa224"
    https://sspai.com/post/99595
    "https://mp.weixin.qq.com/s?__biz=MzAxMDMxOTI2NA==&mid=2649093722&idx=1&sn=363aed81c3119f0a3a874794a83db9df"
    "https://mp.weixin.qq.com/s?__biz=MzkyMDUzMzI5OA==&mid=2247484453&idx=1&sn=31f0fa45982811ab7cadb20a30ec7384"
    "https://mp.weixin.qq.com/s?__biz=Mzk4ODQ0MzkxOA==&mid=2247483799&idx=1&sn=ad8a4623a48710447348ee005808768b&chksm=c415c8971a241af151051a818be0e888d1162c3ee28b2531cdc5e5a61c796fce281bea72aef8&mpshare=1&scene=1&srcid=0527mJnZI0AAqcpbwl6MEEVk&sharer_shareinfo=e49d649aec07082e3a805c92ceac8755&sharer_shareinfo_first=e49d649aec07082e3a805c92ceac8755"
)

for url in ${URLS[*]}; do
    filename="test-$(echo -n "$url" | md5sum | cut -d' ' -f1).md"
    if [ -f "$filename" ]; then
        echo "File $filename already exists, skipping..."
        continue
    fi
    crwl crawl $url -o md-fit -O $filename
done

echo "finish"