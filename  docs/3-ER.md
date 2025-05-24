# ER图

```mermaid
erDiagram
    tb_rss_links{
        int id pK 
        url varchar(255) 
        published_at timestamp
        title varchar(255)
        author varchar(255)
        updated_at timestamp
        created_at timestamp
    }
```
