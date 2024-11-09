from typing import List, Dict, Optional, Union, Tuple
from django.contrib.auth.hashers import make_password
from django.db.models import QuerySet, Q

from apps.capabilities.commerce.models import Organisation
from apps.capabilities.product_management.models import Product
from apps.capabilities.talent.models import Person
from .models import (
    User, 
    ProductRoleAssignment, 
    OrganisationPersonRoleAssignment,
    SignUpRequest,
    SignInAttempt
)


class UserService:
    @staticmethod
    def create(**kwargs) -> User:
        """Create a new user with hashed password"""
        password = kwargs.pop("password")
        user = User(**kwargs)
        if password:
            user.password = make_password(password)
        user.save()
        return user

    @staticmethod
    def create_signup_request(
        user: Optional[User] = None,
        **kwargs
    ) -> SignUpRequest:
        """Create a new signup request"""
        return SignUpRequest.objects.create(user=user, **kwargs)

    @staticmethod
    def record_signin_attempt(
        user: User,
        successful: bool = True,
        **kwargs
    ) -> SignInAttempt:
        """Record a signin attempt"""
        return SignInAttempt.objects.create(
            user=user,
            successful=successful,
            **kwargs
        )

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get a user by email"""
        return User.objects.filter(email=email).first()

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get a user by username"""
        return User.objects.filter(username=username).first()


class RoleService:
    @staticmethod
    def get_product_roles(person: Person, product: Optional[Product] = None) -> QuerySet:
        """
        Get all product roles for a person, optionally filtered by product
        
        Args:
            person: Person object
            product: Optional Product object to filter by
            
        Returns:
            QuerySet of ProductRoleAssignment objects
        """
        query = ProductRoleAssignment.objects.filter(person=person)
        if product:
            query = query.filter(product=product)
        return query.select_related('product')

    @staticmethod
    def get_organisation_roles(
        person: Person, 
        organisation: Optional[Organisation] = None
    ) -> QuerySet:
        """
        Get all organisation roles for a person, optionally filtered by organisation
        
        Args:
            person: Person object
            organisation: Optional Organisation object to filter by
            
        Returns:
            QuerySet of OrganisationPersonRoleAssignment objects
        """
        query = OrganisationPersonRoleAssignment.objects.filter(person=person)
        if organisation:
            query = query.filter(organisation=organisation)
        return query.select_related('organisation')

    @staticmethod
    def has_product_role(
        person: Person, 
        product: Product, 
        roles: Union[str, List[str]]
    ) -> bool:
        """
        Check if person has any of the specified roles for a product
        
        Args:
            person: Person object
            product: Product object
            roles: Single role string or list of role strings
            
        Returns:
            bool indicating if person has any of the specified roles
        """
        if not isinstance(roles, (list, tuple)):
            roles = [roles]
        return ProductRoleAssignment.objects.filter(
            person=person,
            product=product,
            role__in=roles
        ).exists()

    @staticmethod
    def has_organisation_role(
        person: Person, 
        organisation: Organisation, 
        roles: Union[str, List[str]]
    ) -> bool:
        """
        Check if person has any of the specified roles for an organisation
        
        Args:
            person: Person object
            organisation: Organisation object
            roles: Single role string or list of role strings
            
        Returns:
            bool indicating if person has any of the specified roles
        """
        if not isinstance(roles, (list, tuple)):
            roles = [roles]
        return OrganisationPersonRoleAssignment.objects.filter(
            person=person,
            organisation=organisation,
            role__in=roles
        ).exists()

    @staticmethod
    def is_product_admin(person: Person, product: Product) -> bool:
        """Check if person is an admin for the product"""
        return RoleService.has_product_role(
            person, 
            product, 
            ProductRoleAssignment.ProductRoles.ADMIN
        )

    @staticmethod
    def is_product_manager(person: Person, product: Product) -> bool:
        """Check if person is a manager for the product"""
        return RoleService.has_product_role(
            person,
            product,
            ProductRoleAssignment.ProductRoles.MANAGER
        )

    @staticmethod
    def is_organisation_owner(person: Person, organisation: Organisation) -> bool:
        """Check if person is an owner of the organisation"""
        return RoleService.has_organisation_role(
            person,
            organisation,
            OrganisationPersonRoleAssignment.OrganisationRoles.OWNER
        )

    @staticmethod
    def is_organisation_manager(person: Person, organisation: Organisation) -> bool:
        """Check if person is a manager or owner of the organisation"""
        return RoleService.has_organisation_role(
            person,
            organisation,
            [
                OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER
            ]
        )

    @staticmethod
    def get_person_organisations_with_roles(person: Person) -> QuerySet:
        """
        Get all organisations and roles for a person
        
        Returns:
            QuerySet of OrganisationPersonRoleAssignment objects with related organisation
        """
        return OrganisationPersonRoleAssignment.objects.filter(
            person=person
        ).select_related('organisation')

    @staticmethod
    def get_person_products_with_roles(person: Person) -> QuerySet:
        """
        Get all products and roles for a person
        
        Returns:
            QuerySet of ProductRoleAssignment objects with related product
        """
        return ProductRoleAssignment.objects.filter(
            person=person
        ).select_related('product')

    @staticmethod
    def get_person_roles_summary(person: Person) -> Dict:
        """
        Get a summary of all organisations and products the person has access to,
        along with their roles.
        
        Args:
            person: Person object
            
        Returns:
            Dictionary containing:
            {
                'organisations': [
                    {
                        'organisation': Organisation,
                        'role': str
                    },
                    ...
                ],
                'products': [
                    {
                        'product': Product,
                        'role': str
                    },
                    ...
                ]
            }
        """
        org_assignments = RoleService.get_person_organisations_with_roles(person)
        product_assignments = RoleService.get_person_products_with_roles(person)

        return {
            'organisations': [
                {
                    'organisation': assignment.organisation,
                    'role': assignment.role
                }
                for assignment in org_assignments
            ],
            'products': [
                {
                    'product': assignment.product,
                    'role': assignment.role
                }
                for assignment in product_assignments
            ]
        }

    @classmethod
    def assign_product_role(
        cls, 
        person: Person, 
        product: Product, 
        role: str
    ) -> ProductRoleAssignment:
        """
        Assign a role to a person for a product
        
        Args:
            person: Person object
            product: Product object
            role: Role string from ProductRoleAssignment.ProductRoles
            
        Returns:
            Created ProductRoleAssignment object
        """
        assignment, created = ProductRoleAssignment.objects.update_or_create(
            person=person,
            product=product,
            defaults={'role': role}
        )
        return assignment

    @classmethod
    def assign_organisation_role(
        cls, 
        person: Person, 
        organisation: Organisation, 
        role: str
    ) -> OrganisationPersonRoleAssignment:
        """
        Assign a role to a person for an organisation
        
        Args:
            person: Person object
            organisation: Organisation object
            role: Role string from OrganisationPersonRoleAssignment.OrganisationRoles
            
        Returns:
            Created OrganisationPersonRoleAssignment object
        """
        assignment, created = OrganisationPersonRoleAssignment.objects.update_or_create(
            person=person,
            organisation=organisation,
            defaults={'role': role}
        )
        return assignment

    @classmethod
    def remove_product_role(cls, person: Person, product: Product) -> None:
        """Remove all roles for a person in a product"""
        ProductRoleAssignment.objects.filter(
            person=person,
            product=product
        ).delete()

    @classmethod
    def remove_organisation_role(cls, person: Person, organisation: Organisation) -> None:
        """Remove all roles for a person in an organisation"""
        OrganisationPersonRoleAssignment.objects.filter(
            person=person,
            organisation=organisation
        ).delete()

    @staticmethod
    def get_managed_products(person: Person) -> QuerySet:
        """
        Get all products where person:
        1. Has management rights through role assignments
        2. Has management rights through organizations
        3. Is the direct owner (person field)
        """
        # Get organizations where person has management rights
        managed_orgs = Organisation.objects.filter(
            person_role_assignments__person=person,
            person_role_assignments__role__in=[
                OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER
            ]
        )

        # Combine products where:
        # 1. Person has direct management role assignments
        # 2. Products owned by organizations they manage
        # 3. Products where person is the direct owner
        return Product.objects.filter(
            Q(role_assignments__person=person,
              role_assignments__role__in=[
                  ProductRoleAssignment.ProductRoles.ADMIN,
                  ProductRoleAssignment.ProductRoles.MANAGER
              ]) |
            Q(organisation__in=managed_orgs) |
            Q(person=person)  # Add this condition for directly owned products
        ).distinct()

    @staticmethod
    def get_managed_organisations(person: Person) -> QuerySet:
        """Get all organisations where person has management rights"""
        return Organisation.objects.filter(
            person_role_assignments__person=person,
            person_role_assignments__role__in=[
                OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER
            ]
        ).distinct()

    @staticmethod
    def get_product_members(product: Product) -> QuerySet:
        """Get all people with any role in the product"""
        return Person.objects.filter(
            product_roles__product=product
        ).distinct()

    @staticmethod
    def get_organisation_members(organisation: Organisation) -> QuerySet:
        """Get all people with any role in the organisation"""
        return Person.objects.filter(
            organisation_roles__organisation=organisation
        ).distinct()

    @staticmethod
    def get_product_managers(product: Product) -> QuerySet:
        """Get all people with management rights in the product"""
        return Person.objects.filter(
            product_roles__product=product,
            product_roles__role__in=[
                ProductRoleAssignment.ProductRoles.ADMIN,
                ProductRoleAssignment.ProductRoles.MANAGER
            ]
        ).distinct()

    @staticmethod
    def get_organisation_managers(organisation: Organisation) -> QuerySet:
        """Get all people with management rights in the organisation"""
        return Person.objects.filter(
            organisation_roles__organisation=organisation,
            organisation_roles__role__in=[
                OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER
            ]
        ).distinct()

    @staticmethod
    def get_user_products(person: Person) -> QuerySet:
        """
        Get all products where person:
        1. Has any role assignment
        2. Has access through organizations
        3. Is the direct owner
        """
        # Get organizations where person has any role
        user_orgs = Organisation.objects.filter(
            person_role_assignments__person=person
        )

        # Combine products where:
        # 1. Person has any role assignment
        # 2. Products owned by organizations they're part of
        # 3. Products where person is the direct owner
        return Product.objects.filter(
            Q(role_assignments__person=person) |
            Q(organisation__in=user_orgs) |
            Q(person=person)
        ).distinct()

    @staticmethod
    def has_product_access(person: Person, product: Product) -> bool:
        """
        Check if person has access to view the product
        
        Access is granted if person:
        1. Has admin/manager role in the product
        2. Has member role in the product
        3. Is the direct owner of the product
        4. Has access through organization roles
        """
        # Direct product ownership
        if product.person == person:
            return True
            
        # Check product roles (admin, manager, member)
        if ProductRoleAssignment.objects.filter(
            person=person,
            product=product,
            role__in=[
                ProductRoleAssignment.ProductRoles.ADMIN,
                ProductRoleAssignment.ProductRoles.MANAGER,
                ProductRoleAssignment.ProductRoles.MEMBER
            ]
        ).exists():
            return True
            
        # Check organization access
        if product.organisation:
            if OrganisationPersonRoleAssignment.objects.filter(
                person=person,
                organisation=product.organisation,
                role__in=[
                    OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MEMBER
                ]
            ).exists():
                return True
                
        return False

    @staticmethod
    def has_product_management_access(person: Person, product: Product) -> bool:
        """
        Check if person has management-level access to the product
        
        Management access is granted if person:
        1. Has admin role in the product
        2. Has manager role in the product
        3. Is the direct owner of the product
        4. Has owner/manager access through organization roles
        """
        # Direct product ownership
        if product.person == person:
            return True
            
        # Check product roles (admin, manager)
        if ProductRoleAssignment.objects.filter(
            person=person,
            product=product,
            role__in=[
                ProductRoleAssignment.ProductRoles.ADMIN,
                ProductRoleAssignment.ProductRoles.MANAGER
            ]
        ).exists():
            return True
            
        # Check organization access (owner/manager only)
        if product.organisation:
            if OrganisationPersonRoleAssignment.objects.filter(
                person=person,
                organisation=product.organisation,
                role__in=[
                    OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER
                ]
            ).exists():
                return True
                
        return False

    @staticmethod
    def can_access_product_by_visibility(person: Optional[Person], product: Product) -> bool:
        """
        Check if a person can access a product based on its visibility settings
        
        Args:
            person: Optional Person object (None for unauthenticated users)
            product: Product object to check access for
            
        Returns:
            bool indicating if access is allowed
        """
        # GLOBAL products are accessible to everyone
        if product.visibility == Product.Visibility.GLOBAL:
            return True
            
        # All other visibility levels require authentication
        if person is None:
            return False
            
        # ORG_ONLY requires org membership
        if product.visibility == Product.Visibility.ORG_ONLY:
            return RoleService.has_organisation_role(
                person,
                product.organisation,
                [
                    OrganisationPersonRoleAssignment.OrganisationRoles.OWNER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MANAGER,
                    OrganisationPersonRoleAssignment.OrganisationRoles.MEMBER
                ]
            )
            
        # RESTRICTED requires product role
        if product.visibility == Product.Visibility.RESTRICTED:
            return RoleService.has_product_role(
                person,
                product,
                [
                    ProductRoleAssignment.ProductRoles.ADMIN,
                    ProductRoleAssignment.ProductRoles.MANAGER,
                    ProductRoleAssignment.ProductRoles.MEMBER
                ]
            )
        
        return False
