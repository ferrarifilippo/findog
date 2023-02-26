import sqlite3

conn = sqlite3.connect('findog.db')
c = conn.cursor()

c.execute('''
          CREATE TABLE IF NOT EXISTS dog_owner
          ([id] INTEGER PRIMARY KEY, 
          [first_name] TEXT NOT NULL,
          [last_name] TEXT NOT NULL,
          [email] TEXT NOT NULL,
          [address] TEXT NOT NULL,
          [phone] TEXT NOT NULL,
          [dog_id] INTEGER ,
          [password]  TEXT NOT NULL,
          [dog] INTEGER,
          [authenticated] INTEGER,
          
          FOREIGN KEY (dog) 
            REFERENCES dog (dog_id) 
            ON DELETE CASCADE 
            ON UPDATE NO ACTION
            )
          ''')
          
c.execute('''
          CREATE TABLE IF NOT EXISTS dog
          ([uuid] TEXT PRIMARY KEY, 
          [name] TEXT NOT NULL,
          [breed] TEXT NOT NULL,
          [color] TEXT NOT NULL,
          [user] INTEGER,
          [state] TEXT NOT NULL,
          
          FOREIGN KEY (user) 
            REFERENCES dog_owner (user_id) 
            ON DELETE CASCADE 
            ON UPDATE NO ACTION
            )
          ''')
                     
conn.commit()