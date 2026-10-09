import uuid
import random
import hashlib
import re
from typing import Dict, Any, List, Optional
from datetime import timedelta
from sqlalchemy.orm import Session

from backend.app.schemas import GeneratedQuiz, QuizQuestion, QuizOption
from backend.app.models import Quiz, QuizQuestionModel, GeneratedQuestionHistory, utc_now
from backend.app.services.course_gating_service import CourseGatingService
from backend.app.data.catalog_manager import CatalogManager

# In-memory answer key cache for fallback execution
_QUIZ_ANSWER_KEYS: Dict[str, Dict[str, Any]] = {}


# --- TOPIC SPECIFIC QUESTION GENERATION ARCHETYPES ---
# Each archetype has:
# - question_template: string
# - correct_answer: string
# - distractors: list of 3 plausible misconceptions
# - explanation: detailed conceptual reason
# - hint: subtle nudge without giving away answer
# - learning_objective: specific competency being measured
# - difficulty: Beginner | Intermediate | Advanced

TOPIC_QUESTION_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "python": [
        {
            "template": "Which built-in Python data structure is mutable, dynamically sized, and preserves insertion order?",
            "correct": "list",
            "distractors": ["tuple", "frozenset", "str"],
            "explanation": "In Python, lists are mutable sequences that preserve insertion order. Tuples and frozensets are immutable.",
            "hint": "Consider which sequence allows modifying, appending, or removing items in-place.",
            "objective": "Understand built-in collection mutability and ordered sequences",
            "difficulty": "Beginner"
        },
        {
            "template": "What exception is raised when attempting to divide an integer by zero in Python?",
            "correct": "ZeroDivisionError",
            "distractors": ["ValueError", "ArithmeticOverflowError", "TypeError"],
            "explanation": "Python deterministically raises ZeroDivisionError when the denominator of a division or modulo operation is zero.",
            "hint": "Think about arithmetic exception hierarchy in Python's standard library.",
            "objective": "Handle standard Python runtime arithmetic exceptions",
            "difficulty": "Beginner"
        },
        {
            "template": "What is the primary difference between a generator function and a standard function in Python?",
            "correct": "Generators yield values lazily one at a time using 'yield', maintaining state between iterations",
            "distractors": [
                "Generators run asynchronously on separate OS background threads",
                "Generators return all results simultaneously inside a preallocated tuple",
                "Generators can only process floating point and integer numbers"
            ],
            "explanation": "Generators produce items on demand (lazy evaluation) via the yield statement, preserving memory for large data streams.",
            "hint": "Focus on memory footprint and execution resumption.",
            "objective": "Apply generator iteration and lazy evaluation",
            "difficulty": "Intermediate"
        },
        {
            "template": "In Python dictionary implementation, what requirement must an object satisfy to be used as a dictionary key?",
            "correct": "The object must be hashable and implement both __hash__() and __eq__()",
            "distractors": [
                "The object must be an instance of str or int only",
                "The object must be mutable so its value can be updated dynamically",
                "The object must inherit directly from collections.abc.Mapping"
            ],
            "explanation": "Dictionary keys in Python must be hashable (immutable with consistent hash values throughout their lifetime).",
            "hint": "Consider why unhashable types like lists cannot serve as dictionary keys.",
            "objective": "Master hash maps and dictionary key hashing requirements",
            "difficulty": "Intermediate"
        },
        {
            "template": "What occurs when accessing a non-existent key in a standard Python dict using bracket syntax dict[key]?",
            "correct": "Raises KeyError immediately",
            "distractors": [
                "Returns None silently",
                "Creates the key with value None",
                "Raises IndexError"
            ],
            "explanation": "Bracket indexing dict[k] raises KeyError if k is missing. To return a default without an exception, use dict.get(k, default).",
            "hint": "Contrast direct bracket lookup with dict.get().",
            "objective": "Implement defensive key lookup patterns",
            "difficulty": "Beginner"
        },
        {
            "template": "What does the 'is' operator test for in Python, as opposed to the '==' operator?",
            "correct": "Object identity in memory (same memory address), whereas '==' tests value equality",
            "distractors": [
                "Value equality with automatic type coercion",
                "Whether two variables have identical variable name strings",
                "Type inheritance check equivalent to isinstance()"
            ],
            "explanation": "'is' checks whether two references point to the exact same object in memory (id(a) == id(b)), whereas '==' checks equality of values.",
            "hint": "Think about memory identity versus semantic value.",
            "objective": "Distinguish object identity from value equality",
            "difficulty": "Beginner"
        }
    ],
    "c_cpp": [
        {
            "template": "In modern C++, what principle does RAII (Resource Acquisition Is Initialization) dictate?",
            "correct": "Resource lifetimes are bound to object lifetime; acquisition occurs in constructor and release in destructor",
            "distractors": [
                "All memory must be allocated on the heap inside main() before threads start",
                "Garbage collection periodically scans and frees orphaned pointers",
                "Pointers must be cast to void* before deallocation"
            ],
            "explanation": "RAII ensures resources (memory, file handles, mutex locks) are deterministically released when stack-allocated objects exit scope.",
            "hint": "Consider deterministic destruction when a stack frame exits.",
            "objective": "Implement deterministic resource management using RAII",
            "difficulty": "Intermediate"
        },
        {
            "template": "What is the primary danger of returning a pointer or reference to a local stack variable in C or C++?",
            "correct": "The stack frame is popped upon function return, resulting in a dangling pointer to deallocated memory",
            "distractors": [
                "It causes a compiler syntax error during symbol table generation",
                "It forces the compiler to copy the entire heap to virtual memory",
                "It locks the operating system thread pool indefinitely"
            ],
            "explanation": "Local stack variables are destroyed when their enclosing function scope returns. Accessing that pointer invokes undefined behavior.",
            "hint": "Consider the lifetime of stack memory after a return statement.",
            "objective": "Prevent dangling pointers and undefined behavior",
            "difficulty": "Intermediate"
        },
        {
            "template": "In C, which standard library function allocates memory on the heap and initializes all bytes to zero?",
            "correct": "calloc",
            "distractors": ["malloc", "realloc", "zalloc"],
            "explanation": "calloc(num, size) allocates memory and zeroes out all allocated bytes. malloc leaves memory uninitialized.",
            "hint": "Recall the difference between uninitialized malloc and zero-initialized allocation.",
            "objective": "Master dynamic memory allocation in C",
            "difficulty": "Beginner"
        },
        {
            "template": "In C++, why should a base class intended for polymorphic use have a virtual destructor?",
            "correct": "To ensure deleting a derived class through a base class pointer invokes the derived destructor and frees derived resources",
            "distractors": [
                "To prevent child classes from overriding pure virtual methods",
                "To force the compiler to allocate the class on the data segment instead of heap",
                "To allow private members to be inherited by friend functions"
            ],
            "explanation": "Without a virtual destructor, deleting via a base pointer only runs the base destructor, leaking derived class resources.",
            "hint": "Think about what happens when deleting Derived* through Base*.",
            "objective": "Implement safe polymorphic inheritance and cleanup",
            "difficulty": "Intermediate"
        }
    ],
    "java": [
        {
            "template": "In the Java Virtual Machine (JVM), where are object instances allocated?",
            "correct": "On the Heap memory space",
            "distractors": [
                "Directly on the thread's Stack frame",
                "In the Native Method Register only",
                "Inside the CPU L1 hardware cache exclusively"
            ],
            "explanation": "In Java, all objects and array instances are allocated on the Heap and managed by the Garbage Collector. Primitive locals and references reside on the Stack.",
            "hint": "Distinguish where primitive local variables live versus where 'new' allocations reside.",
            "objective": "Understand JVM memory architecture and object allocation",
            "difficulty": "Beginner"
        },
        {
            "template": "What distinguishes a Checked Exception from an Unchecked Exception in Java?",
            "correct": "Checked exceptions subclass Exception (not RuntimeException) and must be caught or declared in throws clause",
            "distractors": [
                "Checked exceptions cause immediate JVM termination without stack traces",
                "Unchecked exceptions can only occur during bytecode compilation",
                "Checked exceptions are only thrown by the operating system kernel"
            ],
            "explanation": "Checked exceptions are verified at compile-time by the Java compiler and require try-catch or throws declarations.",
            "hint": "Consider compile-time enforcement vs RuntimeException descendants.",
            "objective": "Apply Java exception hierarchy rules",
            "difficulty": "Intermediate"
        },
        {
            "template": "In Java multithreading, why is ConcurrentHashMap preferred over Collections.synchronizedMap?",
            "correct": "ConcurrentHashMap uses segmented/bucket-level locking allowing concurrent reads and writes, avoiding global map locking",
            "distractors": [
                "ConcurrentHashMap disables multi-core CPU context switching",
                "Collections.synchronizedMap does not support key-value pairs",
                "ConcurrentHashMap runs in kernel mode via JNI"
            ],
            "explanation": "ConcurrentHashMap achieves high concurrency by avoiding table-wide locks, whereas synchronizedMap locks the entire map for every operation.",
            "hint": "Think about fine-grained bucket synchronization versus global mutexes.",
            "objective": "Design scalable concurrent thread-safe data structures",
            "difficulty": "Advanced"
        }
    ],
    "sql": [
        {
            "template": "What is the key difference between INNER JOIN and LEFT OUTER JOIN in SQL?",
            "correct": "INNER JOIN returns only rows with matches in both tables; LEFT JOIN returns all left table rows plus matching right table rows",
            "distractors": [
                "INNER JOIN modifies the underlying table schema on disk",
                "LEFT JOIN sorts the results in ascending order automatically",
                "INNER JOIN cannot use equality operators in ON conditions"
            ],
            "explanation": "LEFT JOIN preserves all records from the left relation, substituting NULL for missing matches on the right relation.",
            "hint": "Consider what happens to rows in Table A that have no counterpart in Table B.",
            "objective": "Formulate relational joins and understand NULL preservation",
            "difficulty": "Beginner"
        },
        {
            "template": "In relational database systems, what purpose does the HAVING clause serve?",
            "correct": "Filters grouped records based on aggregate function conditions after GROUP BY has been applied",
            "distractors": [
                "Filters individual rows before grouping or indexing takes place",
                "Acts as an alias for the WHERE clause with lower latency",
                "Creates temporary in-memory foreign key constraints"
            ],
            "explanation": "WHERE filters rows before aggregation; HAVING filters aggregate groups (e.g., HAVING COUNT(*) > 5).",
            "hint": "Think about why WHERE cannot contain aggregate expressions like SUM() or AVG().",
            "objective": "Apply aggregate filtering using HAVING and GROUP BY",
            "difficulty": "Intermediate"
        },
        {
            "template": "In transaction management, what does the 'I' in ACID stand for and guarantee?",
            "correct": "Isolation: concurrent transactions execute without interfering with one another's intermediate states",
            "distractors": [
                "Inheritance: tables inherit column constraints from parent schemas",
                "Indexing: every table automatically builds clustered B-Trees",
                "Idempotency: repeating an UPDATE produces zero database writes"
            ],
            "explanation": "Isolation prevents race conditions and dirty reads when multiple transactions execute concurrently.",
            "hint": "Consider transaction boundaries and dirty read prevention.",
            "objective": "Understand database ACID transaction guarantees",
            "difficulty": "Intermediate"
        }
    ],
    "web": [
        {
            "template": "In the browser JavaScript runtime, what role does the Microtask Queue play in the Event Loop?",
            "correct": "Processes Promise callbacks and queueMicrotask jobs immediately after the current synchronous script and before the next rendering/Macrotask",
            "distractors": [
                "Runs Web Worker tasks concurrently on physical background CPU cores",
                "Buffers incoming TCP network packets before HTTP parsing",
                "Executes setTimeout and setInterval callbacks prior to Promises"
            ],
            "explanation": "Microtasks (Promises) execute immediately after the current call stack clears, before macrotasks (setTimeout, UI events) are dequeued.",
            "hint": "Consider Promise resolution priority versus setTimeout(..., 0).",
            "objective": "Master JavaScript Event Loop and asynchronous task ordering",
            "difficulty": "Intermediate"
        },
        {
            "template": "Why should React state not be mutated directly (e.g., state.items.push(item))?",
            "correct": "React detects changes via shallow reference equality; mutating in-place prevents re-rendering and breaks component lifecycle",
            "distractors": [
                "Direct mutation raises an immediate browser security sandbox TypeError",
                "Direct mutation automatically clears the browser's IndexedDB cache",
                "Direct mutation converts objects into immutable read-only Proxies"
            ],
            "explanation": "React relies on immutable state updates to detect differences through reference comparison. Always create a new object/array copy.",
            "hint": "Think about how React determines whether a component needs to re-render.",
            "objective": "Enforce immutable state management in modern UI components",
            "difficulty": "Beginner"
        }
    ],
    "cybersecurity": [
        {
            "template": "What is the primary defense against SQL Injection (SQLi) vulnerabilities in web applications?",
            "correct": "Using Parameterized Queries (Prepared Statements) with bound parameters",
            "distractors": [
                "Encoding SQL strings in Base64 before sending to the database",
                "Filtering out the apostrophe character with simple string replacement",
                "Running the database server on a non-standard port number"
            ],
            "explanation": "Parameterized queries separate the query structure from user data, ensuring input is treated as literal values rather than executable code.",
            "hint": "Focus on separating code interpretation from data parameters.",
            "objective": "Mitigate injection vulnerabilities using prepared statements",
            "difficulty": "Intermediate"
        },
        {
            "template": "In cryptography, how does Asymmetric Encryption differ from Symmetric Encryption?",
            "correct": "Asymmetric encryption uses a public/private keypair; symmetric encryption uses the same shared key for encryption and decryption",
            "distractors": [
                "Asymmetric encryption only works over unencrypted UDP network protocols",
                "Symmetric encryption requires a Certificate Authority signature for every message",
                "Asymmetric encryption does not support hashing or digital signatures"
            ],
            "explanation": "Asymmetric cryptography (e.g. RSA, ECC) relies on mathematically linked keypairs, enabling secure key exchange without shared secrets.",
            "hint": "Think about public versus private key roles.",
            "objective": "Apply symmetric and asymmetric encryption principles",
            "difficulty": "Beginner"
        }
    ],
    "general": [
        {
            "template": "What is the time complexity of searching for an element in an unsorted array of size N in the worst case?",
            "correct": "O(N) linear time",
            "distractors": ["O(log N) logarithmic time", "O(1) constant time", "O(N^2) quadratic time"],
            "explanation": "In an unsorted array, linear search must inspect up to all N elements in the worst case.",
            "hint": "Consider scanning elements sequentially from index 0 to N-1.",
            "objective": "Analyze algorithmic time complexities",
            "difficulty": "Beginner"
        },
        {
            "template": "In system design, what does Horizontal Scaling (Scale-Out) refer to?",
            "correct": "Adding more machine nodes/instances to distribute workload across a cluster",
            "distractors": [
                "Upgrading CPU, RAM, and SSD capacity on a single existing server instance",
                "Converting relational SQL tables into unindexed CSV files",
                "Compressing HTTP request headers using GZIP"
            ],
            "explanation": "Horizontal scaling involves distributing load across multiple smaller servers, offering high availability and fault tolerance.",
            "hint": "Distinguish adding more servers versus upgrading one single machine.",
            "objective": "Design scalable distributed system architectures",
            "difficulty": "Intermediate"
        }
    ]
}


def _normalize_question_text(text: str) -> str:
    """Produces clean normalized representation of question text for hashing."""
    return re.sub(r'\s+', ' ', text.strip().lower())


def _compute_question_hash(normalized_text: str) -> str:
    """Computes deterministic SHA-256 hash of normalized question content."""
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def _get_archetypes_for_topic(topic: str) -> List[Dict[str, Any]]:
    """Resolves relevant question archetypes matching the topic."""
    norm = CatalogManager.normalize_skill_name(topic).lower()
    
    for key, pool in TOPIC_QUESTION_TEMPLATES.items():
        if key in norm:
            return pool

    if "python" in norm:
        return TOPIC_QUESTION_TEMPLATES["python"]
    elif "c++" in norm or "c " in norm or "pointer" in norm:
        return TOPIC_QUESTION_TEMPLATES["c_cpp"]
    elif "java" in norm:
        return TOPIC_QUESTION_TEMPLATES["java"]
    elif "sql" in norm or "database" in norm:
        return TOPIC_QUESTION_TEMPLATES["sql"]
    elif "web" in norm or "react" in norm or "javascript" in norm or "css" in norm:
        return TOPIC_QUESTION_TEMPLATES["web"]
    elif "security" in norm or "cipher" in norm:
        return TOPIC_QUESTION_TEMPLATES["cybersecurity"]
    
    return TOPIC_QUESTION_TEMPLATES["general"] + TOPIC_QUESTION_TEMPLATES["python"]


def generate_quiz(
    student_id: int,
    topic: str,
    num_questions: int = 5,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Fresh MCQ Generation Engine:
    - Enforces course-completion gating state machine (rejects locked access).
    - Exclusively outputs single-answer Multiple-Choice Questions (4 options: A, B, C, D).
    - Employs SHA-256 deduplication hashing against recent student quiz history.
    - Server-side answer keys and explanations stored securely in DB.
    - Options randomized safely with updated expected answer indices.
    """
    # 1. Authoritative Course-Completion Gating Check
    if db is not None:
        can_access, state, lock_reason = CourseGatingService.can_access_quiz(student_id, topic, db)
        if not can_access:
            raise ValueError(f"Quiz locked: {lock_reason}")

    course_info = CourseGatingService.get_course_info_for_topic(topic)
    course_id = course_info["course_id"]
    difficulty = course_info["difficulty"]

    # 2. Fetch student's recent question hashes for this topic to prevent repetition
    recent_hashes = set()
    if db is not None:
        history_records = db.query(GeneratedQuestionHistory).filter(
            GeneratedQuestionHistory.student_id == student_id,
            GeneratedQuestionHistory.topic == topic
        ).order_by(GeneratedQuestionHistory.created_at.desc()).limit(20).all()
        recent_hashes = {r.question_hash for r in history_records}

    # 3. Select Archetypes and Generate Fresh MCQs
    archetypes = _get_archetypes_for_topic(topic)
    random.seed()  # Ensure high entropy across requests

    # Filter out recently used questions if alternative fresh questions exist
    fresh_archetypes = [
        arch for arch in archetypes
        if _compute_question_hash(_normalize_question_text(arch["template"])) not in recent_hashes
    ]

    # If all archetypes were used in history, cycle back to the full pool
    pool = fresh_archetypes if len(fresh_archetypes) >= num_questions else archetypes
    selected_archetypes = random.sample(pool, min(num_questions, len(pool)))

    quiz_id = f"quiz_{uuid.uuid4().hex[:8]}"
    questions_for_client: List[QuizQuestion] = []
    server_keys: Dict[str, Dict[str, Any]] = {}
    new_history_records: List[GeneratedQuestionHistory] = []

    for idx, arch in enumerate(selected_archetypes):
        q_id = f"{quiz_id}_q{idx + 1}"
        q_text = arch["template"]
        correct_text = arch["correct"]
        distractors = list(arch["distractors"][:3])

        # Ensure exactly 4 distinct choices
        raw_options = [correct_text] + distractors
        random.shuffle(raw_options)

        # Build options A, B, C, D
        option_letters = ["A", "B", "C", "D"]
        options: List[QuizOption] = []
        correct_letter = "A"

        for opt_idx, text in enumerate(raw_options):
            letter = option_letters[opt_idx]
            options.append(QuizOption(option_id=letter, text=text))
            if text == correct_text:
                correct_letter = letter

        # Student-facing question schema (Strictly Multiple Choice Only)
        client_q = QuizQuestion(
            id=q_id,
            question_type="multiple_choice",
            question_text=q_text,
            options=options,
            hint=arch.get("hint"),
            course_id=course_id,
            topic_id=f"topic_{re.sub(r'[^a-z0-9]+', '_', topic.lower()).strip('_')}",
            learning_objective=arch.get("objective"),
            difficulty=arch.get("difficulty", difficulty),
            created_at=utc_now().isoformat()
        )
        questions_for_client.append(client_q)

        # Server-side private key data
        server_keys[q_id] = {
            "expected_answer": correct_letter,
            "question_type": "multiple_choice",
            "explanation": arch["explanation"],
            "keywords": [correct_text.lower(), correct_letter.lower()],
            "question_text": q_text,
            "options_json": [opt.model_dump() for opt in options],
            "hint": arch.get("hint")
        }

        # Track question hash for deduplication
        q_hash = _compute_question_hash(_normalize_question_text(q_text))
        new_history_records.append(
            GeneratedQuestionHistory(
                student_id=student_id,
                course_id=course_id,
                topic=topic,
                question_hash=q_hash,
                question_text=q_text,
                difficulty=arch.get("difficulty", difficulty)
            )
        )

    # 4. Persist Quiz, Questions, and History in DB
    if db is not None:
        db_quiz = Quiz(
            quiz_id=quiz_id,
            student_id=student_id,
            topic=topic,
            status="active",
            created_at=utc_now(),
            expires_at=utc_now() + timedelta(hours=2)
        )
        db.add(db_quiz)
        db.flush()

        for q in questions_for_client:
            s_key = server_keys[q.id]
            db_q = QuizQuestionModel(
                question_id=q.id,
                quiz_db_id=db_quiz.id,
                question_type="multiple_choice",
                question_text=q.question_text,
                options_json=[opt.model_dump() for opt in q.options],
                hint=q.hint,
                expected_answer=s_key["expected_answer"],
                explanation=s_key["explanation"],
                keywords_json=s_key["keywords"]
            )
            db.add(db_q)

        for hist in new_history_records:
            db.add(hist)

        db.commit()

    # Cache answer keys in memory for fallback / direct execution
    _QUIZ_ANSWER_KEYS[quiz_id] = server_keys

    generated_quiz = GeneratedQuiz(
        quiz_id=quiz_id,
        topic=topic,
        course_id=course_id,
        difficulty=difficulty,
        learning_objective=course_info.get("learning_objectives", ["Master topic"])[0],
        questions=questions_for_client
    )

    return generated_quiz.model_dump()


def get_quiz_answer_key(quiz_id: str) -> Dict[str, Dict[str, Any]]:
    """Helper to retrieve answer key for evaluation."""
    return _QUIZ_ANSWER_KEYS.get(quiz_id, {})

