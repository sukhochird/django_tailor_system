from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from customers.models import Customer
from employees.models import Employee
from materials.models import Material


class Order(models.Model):
    STATUS_CHOICES = [
        ('order_placed', 'Захиалга өгсөн'),
        ('material_arrived', 'Материал ирсэн'),
        ('cutter_cutting', 'Эсгүүрчин эсгэсэн'),
        ('customer_first_fitting', 'Үйлчлүүлэгч 1-р хэмжээ өмссөн'),
        ('tailor_first_completion', 'Эсгүүрчин 1-р хэмжээ миллэсэн'),
        ('seamstress_second_prep', 'Оёдолчин 2-р хэмжээ бэлдсэн'),
        ('customer_second_fitting', 'Үйлчлүүлэгч 2-р хэмжээ өмссөн'),
        ('tailor_second_completion', 'Эсгүүрчин 2-р хэмжээ миллэсэн'),
        ('seamstress_finished', 'Оёдолчин оёж дууссан'),
    ]
    
    ITEM_TYPE_CHOICES = [
        ('men_suit', 'Эрэгтэй костюм'),
        ('women_suit', 'Эмэгтэй костюм'),
        ('wedding_dress', 'Хуримын даашинз'),
        ('formal_dress', 'Албан ёсны даашинз'),
        ('casual_shirt', 'Энгийн цамц'),
        ('trousers', 'Өмд'),
        ('jacket', 'Пиджак'),
        ('vest', 'Жилэт'),
        ('coat', 'Пальто'),
        ('repair', 'Хувцас засвар'),
        ('other', 'Бусад'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Үйлчлүүлэгч")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Захиалгын дугаар")
    item_type = models.CharField(max_length=50, choices=ITEM_TYPE_CHOICES, verbose_name="Хувцасны төрөл")
    material_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="Материалын код")
    
    # Design images
    design_front = models.ImageField(upload_to='order_designs/front/', blank=True, null=True, verbose_name="Урд талын загвар")
    design_back = models.ImageField(upload_to='order_designs/back/', blank=True, null=True, verbose_name="Хойд талын загвар")
    design_side = models.ImageField(upload_to='order_designs/side/', blank=True, null=True, verbose_name="Хажуугийн загвар")
    design_reference = models.ImageField(upload_to='order_designs/reference/', blank=True, null=True, verbose_name="Жишээ загвар")
    
    # Томилогдсон ажилтнууд
    assigned_tailor = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tailor_orders',
        verbose_name="Оёдолчин"
    )
    assigned_cutter = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cutter_orders',
        verbose_name="Эсгүүрчин"
    )
    assigned_trouser_maker = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='trouser_maker_orders',
        verbose_name="Өмдний оёдолчин"
    )
    assigned_shirt_cutter = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='shirt_cutter_orders',
        verbose_name="Цамцны эсгүүрчин"
    )
    assigned_shirt_sewer = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='shirt_sewer_orders',
        verbose_name="Цамцны оёдолчин"
    )
    
    # Цамцтай эсэх
    has_shirt = models.BooleanField(default=False, verbose_name="Цамцтай")
    
    # Үнийн мэдээлэл
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Нийт дүн"
    )
    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Урьдчилгаа дүн"
    )
    
    # Огнооны мэдээлэл
    start_date = models.DateField(verbose_name="Эхлэх огноо")
    due_date = models.DateField(verbose_name="Дуусах огноо")
    completed_date = models.DateField(null=True, blank=True, verbose_name="Дууссан огноо")
    
    # Статус
    current_status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        default='order_placed',
        verbose_name="Одоогийн статус"
    )
    
    # Нэмэлт мэдээлэл
    notes = models.TextField(blank=True, null=True, verbose_name="Тэмдэглэл")
    is_rated = models.BooleanField(default=False, verbose_name="Үнэлгээ өгсөн")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Бүртгэсэн огноо")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Сүүлд шинэчлэгдсэн огноо")
    
    class Meta:
        verbose_name = "Захиалга"
        verbose_name_plural = "Захиалга"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.full_name}"
    
    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.current_status, self.current_status)
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.current_status != 'seamstress_finished'
    
    @property
    def progress_percentage(self):
        status_order = [choice[0] for choice in self.STATUS_CHOICES]
        current_index = status_order.index(self.current_status)
        return int((current_index + 1) / len(status_order) * 100)
    
    @property
    def days_remaining(self):
        """Calculate days remaining until due date"""
        from django.utils import timezone
        today = timezone.now().date()
        days = (self.due_date - today).days
        return days
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount after advance payment.
        
        If advance amount is zero (default), treat the order as fully paid.
        """
        total = self.total_amount or Decimal('0')
        advance = self.advance_amount or Decimal('0')
        
        if advance == Decimal('0'):
            return Decimal('0')
        
        remaining = total - advance
        if remaining < Decimal('0'):
            return Decimal('0')
        return remaining
    
    def get_status_color(self):
        """Return CSS class for status badge"""
        colors = {
            'seamstress_finished': 'bg-green-100 text-green-800',
            'customer_first_fitting': 'bg-yellow-100 text-yellow-800',
            'customer_second_fitting': 'bg-yellow-100 text-yellow-800',
            'cutter_cutting': 'bg-yellow-100 text-yellow-800',
            'order_placed': 'bg-blue-100 text-blue-800',
            'material_arrived': 'bg-blue-100 text-blue-800',
        }
        return colors.get(self.current_status, 'bg-gray-100 text-gray-800')
    
    def is_status_completed(self, status_code):
        """Check if a specific status has been completed"""
        return self.status_history.filter(status=status_code).exists()
    
    def get_status_completion_info(self, status_code):
        """Get completion information for a specific status"""
        try:
            history = self.status_history.filter(status=status_code).first()
            if history:
                return {
                    'completed_by': history.completed_by,
                    'completed_at': history.completed_at,
                    'notes': history.notes
                }
        except:
            pass
        return None


class OrderStatusHistory(models.Model):
    """Track the history of order status changes"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history', verbose_name="Захиалга")
    status = models.CharField(max_length=50, choices=Order.STATUS_CHOICES, verbose_name="Статус")
    completed_by = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Дуусгасан хүн")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дууссан огноо")
    notes = models.TextField(blank=True, null=True, verbose_name="Тэмдэглэл")
    
    class Meta:
        verbose_name = "Захиалгын статусын түүх"
        verbose_name_plural = "Захиалгын статусын түүх"
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"


class ProcessStep(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Хүлээгдэж буй'),
        ('in_progress', 'Хийгдэж байгаа'),
        ('completed', 'Дууссан'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='process_steps', verbose_name="Захиалга")
    step_type = models.CharField(max_length=50, verbose_name="Алхамын төрөл")
    title = models.CharField(max_length=100, verbose_name="Гарчиг")
    description = models.TextField(verbose_name="Тайлбар")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="Дууссан огноо")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Бүртгэсэн огноо")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Сүүлд шинэчлэгдсэн огноо")
    
    class Meta:
        verbose_name = "Үйл явцын алхам"
        verbose_name_plural = "Үйл явцын алхамууд"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.title}"


class OrderRating(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='rating', verbose_name="Захиалга")
    overall_rating = models.IntegerField(verbose_name="Ерөнхий үнэлгээ")
    quality_rating = models.IntegerField(verbose_name="Чанарын үнэлгээ")
    service_rating = models.IntegerField(verbose_name="Үйлчилгээний үнэлгээ")
    timing_rating = models.IntegerField(verbose_name="Хугацааны үнэлгээ")
    comments = models.TextField(blank=True, null=True, verbose_name="Сэтгэгдэл")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Үнэлгээ өгсөн огноо")
    
    class Meta:
        verbose_name = "Захиалгын үнэлгээ"
        verbose_name_plural = "Захиалгын үнэлгээнүүд"
    
    def __str__(self):
        return f"{self.order.order_number} - {self.overall_rating}/5 үнэлгээ"


class EmployeeRating(models.Model):
    """Ажилтануудад өгөх үнэлгээ"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='employee_ratings', verbose_name="Захиалга")
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='ratings', verbose_name="Ажилтан")
    rating = models.IntegerField(verbose_name="Үнэлгээ", help_text="1-5")
    comment = models.TextField(blank=True, null=True, verbose_name="Сэтгэгдэл")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Үнэлгээ өгсөн огноо")
    
    class Meta:
        verbose_name = "Ажилтны үнэлгээ"
        verbose_name_plural = "Ажилтнуудын үнэлгээнүүд"
        unique_together = ['order', 'employee']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.employee.full_name}: {self.rating}/5"