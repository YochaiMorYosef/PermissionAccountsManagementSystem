## Future improvements:

1. JWT authentication - I would add a real authorizer with signature and validity checking
2. DB Indexes - Improve database indexing to better support access patterns and avoid heavy filtering operations.
3. Cashing - Add caching and incremental data loading to improve rendering performance and scrolling experience when displaying large permission lists.
4. More Test - Add additional tests to cover edge cases, including the discovered bug scenario and the new role-based access control logic.
5. Logging and error handaling - Adding clear logs and error handaling for the rellvants parts in the code, such as at the beginning of the application upload, in each patch of information, etc.
6. UI - Impeove the UI by adding a proper authentication flow (login) and improving overall usability and user experience.
7. UX - Improve the overall UX by making the interface more intuitive, with clearer feedback.